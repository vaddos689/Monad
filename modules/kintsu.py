import asyncio
import random
from loguru import logger
from utils_accs import write_result
from general_settings import semaphore, KINTSU_STAKE_RANGE, KINTSU_UNSTAKE_ALL, KINTSU_UNSTAKE_PRECENT
from config import KINTSU_ABI, KINTSU_CONTRACT
from modules.client import Client
from decimal import Decimal, ROUND_FLOOR

def get_random_float_from_range(range_: list):
    return round(random.uniform(range_[0], range_[1]), 4)

class Kintsu:
    def __init__(self, account) -> None:
        self.account = account
        self.id = account['id']
        self.private_key = account['private_key']
        self.proxy = account['proxy']
        # Without Proxy (integrate only with blockchain)
        self.client = Client(self.id, self.private_key)
        
        self.kintsu_contract = self.client.get_contract(KINTSU_CONTRACT, KINTSU_ABI)

    async def get_smon_balance(self):
        sMON_balance_in_wei, sMON_balance, _ = await self.client.get_token_balance('sMON')
        balance = Decimal(str(sMON_balance)).to_eng_string().replace('E', 'e')
        logger.info(f'[{self.id}] [{self.client.address}] sMON balance: {balance}')
        return balance

    async def stake_mon(self):
        random_stake_amount = get_random_float_from_range(KINTSU_STAKE_RANGE)
        logger.info(f'[{self.id}] [{self.client.address}] random stake amount MON: {random_stake_amount}')
        
        wallet_balance_in_wei, wallet_balance, _ = await self.client.get_token_balance(check_native=True)
        
        logger.info(f'[{self.id}] [{self.client.address}] Wallet balance MON: {wallet_balance}')
        if wallet_balance < random_stake_amount:
            logger.info(f'[{self.id}] [{self.client.address}] wallet balance < stake amount. skip')
            return
        
        random_stake_amount_wei = int(random_stake_amount * 10 ** 18)
        transaction = await self.kintsu_contract.functions.stake(
        ).build_transaction(await self.client.prepare_transaction(value=random_stake_amount_wei))

        return await self.client.send_transaction(transaction, need_hash=True)

    def round_to_min_step(self, value, min_value=0.0001):
        d = Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_FLOOR)
        return max(d, Decimal(str(min_value)))

    async def unstake_mon(self):
        sMON_balance_in_wei, sMON_balance, _ = await self.client.get_token_balance('sMON')
        
        logger.info(f'[{self.id}] [{self.client.address}] sMON balance: {sMON_balance} MON')
        
        if KINTSU_UNSTAKE_ALL:
            unstake_amount_mon = sMON_balance
            rounded_amount_mon = self.round_to_min_step(unstake_amount_mon)
            shares = int(rounded_amount_mon * 10**18)
            logger.info(f'[{self.id}] [{self.client.address}] unstake all {self.client.w3.from_wei(shares, 'ether')} aprMON')
        else:
            unstake_amount_mon = (KINTSU_UNSTAKE_PRECENT / 100) * sMON_balance
            rounded_amount_mon = self.round_to_min_step(unstake_amount_mon)
            shares = int(rounded_amount_mon * 10**18)
            logger.info(f'[{self.id}] [{self.client.address}] unstake {KINTSU_UNSTAKE_PRECENT}% aprMON == {self.client.w3.from_wei(shares, 'ether')}')        
        
        transaction = await self.kintsu_contract.functions.requestUnlock(
            shares
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction, need_hash=True)


async def start_kintsu(account, action):
    async with semaphore:
        kintsu = Kintsu(account)

        if action == 'stake':
            logger.info(f'Start [{kintsu.id}] account (stake)')
            tx_hash = await kintsu.stake_mon()
            
            if tx_hash:
                result_text = f'{kintsu.client.address} {kintsu.private_key} KINTSU_STAKE {tx_hash.hex()}\n'
                write_result(result_text)

            await kintsu.client.session.close()

        if action == 'unstake':
            logger.info(f'Start [{kintsu.id}] account (unstake)')
            tx_hash = await kintsu.unstake_mon()

            if tx_hash:
                result_text = f'{kintsu.client.address} {kintsu.private_key} KINTSU_UNSTAKE_REQUEST {tx_hash.hex()}\n'
                write_result(result_text)

            await kintsu.client.session.close()
        
        if action == 'balance':
            logger.info(f'Start [{kintsu.id}] account (balance checker)')
            balance = await kintsu.get_smon_balance()

            result_text = f'{kintsu.client.address} {kintsu.private_key} KINTSU_STAKE_BALANCE {balance}\n'
            write_result(result_text)

            await kintsu.client.session.close()



async def start_accounts_for_kintsu(accounts, action):
    task = []
    for account in accounts:
        task.append(asyncio.create_task(start_kintsu(account, action)))

    await asyncio.gather(*task)
    logger.info('Kintsu work completed')
