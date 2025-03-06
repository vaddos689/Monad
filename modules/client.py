import asyncio
import random
import ssl
from loguru import logger
from asyncio import sleep
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector
from web3.exceptions import TransactionNotFound, TimeExhausted
from modules.interfaces import BlockchainException, SoftwareException
from utils.networks import MonadRPC
from config import ERC20_ABI, TOKENS_PER_CHAIN
from web3 import AsyncHTTPProvider, AsyncWeb3


class Client:
    def __init__(
            self, account_id: str | int, private_key: str, proxy: None | str = None
    ):
        self.network = MonadRPC
        self.eip1559_support = MonadRPC.eip1559_support
        self.token = MonadRPC.token
        self.explorer = MonadRPC.explorer
        self.chain_id = MonadRPC.chain_id

        self.proxy_init = proxy
        if proxy:
            self.session = ClientSession(connector=ProxyConnector.from_url(f'http://{proxy}', ssl=ssl.create_default_context(), verify_ssl=True))
        else:
            self.session = ClientSession()
        self.session.headers.update({
            'User-Agent': self.get_user_agent()
        })
        # self.request_kwargs = {"proxy": f"http://{proxy}", "verify_ssl": False} if proxy else {"verify_ssl": False}
        self.request_kwargs = {"verify_ssl": False}
        self.rpc = random.choice(MonadRPC.rpc)
        self.w3 = AsyncWeb3(AsyncHTTPProvider(self.rpc, request_kwargs=self.request_kwargs))
        self.account_id = str(account_id)
        self.private_key = private_key
        self.address = AsyncWeb3.to_checksum_address(self.w3.eth.account.from_key(private_key).address)
        self.acc_info = account_id, self.address

    @staticmethod
    def round_amount(min_amount: float, max_amount: float) -> float:
        decimals = max(len(str(min_amount)) - 1, len(str(max_amount)) - 1)
        return round(random.uniform(min_amount, max_amount), decimals + 2)

    @staticmethod
    def get_user_agent():
        random_version = f"{random.uniform(520, 540):.2f}"
        return (f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{random_version}'
                f' (KHTML, like Gecko) Chrome/121.0.0.0 Safari/{random_version} Edg/121.0.0.0')

    @staticmethod
    def get_normalize_error(error):
        try:
            if isinstance(error.args[0], dict):
                error = error.args[0].get('message', error)
            return error
        except:
            return error

    async def change_rpc(self):
        logger.warning(f'[{self.account_id}] [{self.address}] Trying to replace RPC')

        if len(self.network.rpc) != 1:
            rpcs_list = [rpc for rpc in self.network.rpc if rpc != self.rpc]
            new_rpc = random.choice(rpcs_list)
            self.w3 = AsyncWeb3(AsyncHTTPProvider(new_rpc, request_kwargs=self.request_kwargs))
            logger.success(f'[{self.account_id}] [{self.address}] RPC successfully replaced. New RPC: {new_rpc}')
        else:
            logger.warning(f'[{self.account_id}] [{self.address}] This network has only 1 RPC, no replacement is possible')

    async def get_decimals(self, token_name: str):
        contract = self.get_contract(TOKENS_PER_CHAIN[self.network.name][token_name])
        return await contract.functions.decimals().call()

    async def get_token_balance(
            self, token_name: str = 'ETH', check_symbol: bool = True, check_native: bool = False
    ) -> [float, int, str]:
        if not check_native:
            if token_name != self.network.token:
                contract = self.get_contract(TOKENS_PER_CHAIN[self.network.name][token_name])

                amount_in_wei = await contract.functions.balanceOf(self.address).call()
                decimals = await contract.functions.decimals().call()

                if check_symbol:
                    symbol = await contract.functions.symbol().call()
                    return amount_in_wei, amount_in_wei / 10 ** decimals, symbol
                return amount_in_wei, amount_in_wei / 10 ** decimals, ''

        amount_in_wei = await self.w3.eth.get_balance(self.address)
        return amount_in_wei, amount_in_wei / 10 ** 18, self.network.token

    def get_contract(self, contract_address: str, abi=ERC20_ABI):
        return self.w3.eth.contract(
            address=AsyncWeb3.to_checksum_address(contract_address),
            abi=abi
        )

    async def get_allowance(self, token_address: str, spender_address: str) -> int:
        contract = self.get_contract(token_address)
        return await contract.functions.allowance(
            self.address,
            spender_address
        ).call()

    async def get_priotiry_fee(self):
        fee_history = await self.w3.eth.fee_history(25, 'latest', [20.0])
        non_empty_block_priority_fees = [fee[0] for fee in fee_history["reward"] if fee[0] != 0]

        divisor_priority = max(len(non_empty_block_priority_fees), 1)

        priority_fee = int(round(sum(non_empty_block_priority_fees) / divisor_priority))

        return priority_fee

    async def prepare_transaction(self, value: int = 0):
        try:
            tx_params = {
                'from': self.w3.to_checksum_address(self.address),
                'nonce': await self.w3.eth.get_transaction_count(self.address),
                'value': value,
                'chainId': self.network.chain_id
            }

            if self.network.eip1559_support:

                base_fee = await self.w3.eth.gas_price
                max_priority_fee_per_gas = await self.get_priotiry_fee()
                max_fee_per_gas = base_fee + max_priority_fee_per_gas

                tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
                tx_params['maxFeePerGas'] = int(max_fee_per_gas * 1.5)
                tx_params['type'] = '0x2'
            else:
                tx_params['gasPrice'] = int(await self.w3.eth.gas_price * 1.5)

            return tx_params
        except Exception as error:
            raise BlockchainException(f'{self.get_normalize_error(error)}')

    async def make_approve(self, token_address: str, spender_address: str, amount_in_wei: int):
        transaction = await self.get_contract(token_address).functions.approve(
            spender_address,
            amount=amount_in_wei
        ).build_transaction(await self.prepare_transaction())

        return await self.send_transaction(transaction)

    async def check_for_approved(self, token_address: str, spender_address: str,
                                 amount_in_wei: int, without_bal_check: bool = False) -> bool:
        try:
            contract = self.get_contract(token_address)

            balance_in_wei = await contract.functions.balanceOf(self.address).call()
            symbol = await contract.functions.symbol().call()

            logger.info(f'[{self.account_id}] [{self.address}] Check for approval {symbol}')

            if not without_bal_check and balance_in_wei <= 0:
                raise SoftwareException(f'Zero {symbol} balance')

            approved_amount_in_wei = await self.get_allowance(
                token_address=token_address,
                spender_address=spender_address
            )

            if amount_in_wei <= approved_amount_in_wei:
                logger.info(f'[{self.account_id}] [{self.address}] Already approved')
                return False

            result = await self.make_approve(token_address, spender_address, amount_in_wei)

            await sleep(random.randint(5, 9))
            return result
        except Exception as error:
            raise BlockchainException(f'{self.get_normalize_error(error)}')

    async def send_transaction(self, transaction, need_hash: bool = False, without_gas: bool = False,
                               poll_latency: int = 10, timeout: int = 360):
        try:
            if not without_gas:
                transaction['gas'] = int((await self.w3.eth.estimate_gas(transaction)) * 1.5)
        except Exception as error:
            raise BlockchainException(f'{self.get_normalize_error(error)}')

        try:
            singed_tx = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            tx_hash = await self.w3.eth.send_raw_transaction(singed_tx.rawTransaction)
        except Exception as error:
            if self.get_normalize_error(error) == 'already known':
                logger.warning(f'[{self.account_id}] [{self.address}] RPC got error, but tx was send')
                return True
            else:
                raise BlockchainException(f'{self.get_normalize_error(error)}')

        try:

            total_time = 0
            timeout = timeout if self.network.name != 'Polygon' else 1200

            while True:
                try:
                    receipts = await self.w3.eth.get_transaction_receipt(tx_hash)
                    status = receipts.get("status")
                    if status == 1:
                        message = f'Transaction was successful: {self.explorer}tx/{tx_hash.hex()}'
                        logger.success(f'[{self.account_id}] [{self.address}] {message}')
                        if need_hash:
                            return tx_hash
                        return True
                    elif status is None:
                        await asyncio.sleep(poll_latency)
                    else:
                        return SoftwareException(f'Transaction failed: {self.explorer}tx/{tx_hash.hex()}')
                except TransactionNotFound:
                    if total_time > timeout:
                        if self.network.name in ['BNB Chain', 'Moonbeam']:
                            logger.warning(f'[{self.account_id}] [{self.address}] Transaction was sent and tried to be confirmed, but not finished yet')
                            return True
                        raise TimeExhausted(f"Transaction is not in the chain after {timeout} seconds")
                    total_time += poll_latency
                    await asyncio.sleep(poll_latency)

                except Exception as error:
                    logger.warning(f'[{self.account_id}] [{self.address}] RPC got autims response. Error: {error}')
                    total_time += poll_latency
                    await asyncio.sleep(poll_latency)
        except Exception as error:
            raise BlockchainException(f'{self.get_normalize_error(error)}')