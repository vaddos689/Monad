import asyncio
import random
from loguru import logger
from utils_accs import write_result
from general_settings import semaphore
from modules.client import Client
from config import OWLTO_BYTECODE

class Owlto:
    def __init__(self, account) -> None:
        self.account = account
        self.id = account['id']
        self.private_key = account['private_key']
        self.proxy = account['proxy']
        # Without Proxy (integrate only with blockchain)
        self.client = Client(self.id, self.private_key)
    
    async def get_gas_params(self):
        """Get current gas parameters from the network."""
        latest_block = await self.client.w3.eth.get_block("latest")
        base_fee = latest_block["baseFeePerGas"]
        max_priority_fee = await self.client.w3.eth.max_priority_fee

        # Calculate maxFeePerGas (base fee + priority fee)
        max_fee = base_fee + max_priority_fee

        return {
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": max_priority_fee,
        }
    
    async def estimate_gas(self, transaction: dict) -> int:
        """Estimate gas for transaction and add some buffer."""
        try:
            estimated = await self.client.w3.eth.estimate_gas(transaction)
            return int(estimated * 1.1)
        except Exception as e:
            logger.warning(
                f"[{self.id}] Error estimating gas: {e}. Using default gas limit"
            )
            raise e

    async def deploy_contract(self):
        gas_params = await self.get_gas_params()

        transaction = {
            "from": self.client.address,
            "data": OWLTO_BYTECODE,
            "chainId": 10143,
            "type": 2,
            "value": 0,
        }

        estimated_gas = await self.estimate_gas(transaction)
        
        logger.info(f'[{self.id}] [{self.client.address}] Estimated deploy contract gas: {estimated_gas}')
        
        transaction.update(
                    {
                        "nonce": await self.client.w3.eth.get_transaction_count(
                            self.client.address,
                            "latest",
                        ),
                        "gas": estimated_gas,
                        **gas_params,
                    }
        )
        
        return await self.client.send_transaction(transaction, need_hash=True)

async def start_owlto(account):
    async with semaphore:
        owlto = Owlto(account)

        logger.info(f'Start [{owlto.id}] account')
        tx_hash = await owlto.deploy_contract()
        
        if tx_hash:
            result_text = f'{owlto.client.address} {owlto.private_key} OWLTO_DEPLOY_CONTRACT {tx_hash.hex()}\n'
            write_result(result_text)

        await owlto.client.session.close()


async def start_accounts_for_owlto(accounts):
    task = []
    for account in accounts:
        task.append(asyncio.create_task(start_owlto(account)))

    await asyncio.gather(*task)
