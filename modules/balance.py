import asyncio
import random
from loguru import logger
from utils_accs import write_balance_result
from general_settings import semaphore
from modules.client import Client

class Balance:
    def __init__(self, account) -> None:
        self.account = account
        self.id = account['id']
        self.private_key = account['private_key']
        self.proxy = account['proxy']
        # Without Proxy (integrate only with blockchain)
        self.client = Client(self.id, self.private_key)

    async def get_balance(self):
        wallet_balance_in_wei, wallet_balance, _ = await self.client.get_token_balance(check_native=True)
        
        logger.info(f'[{self.id}] [{self.client.address}] Wallet balance MON: {wallet_balance}')
        return wallet_balance


async def start_checker(account):
    async with semaphore:
        balance = Balance(account)
        logger.info(f'Start [{balance.id}] account')
        
        mon_eth_balance = await balance.get_balance()
        
        text = f'{balance.client.address} {balance.client.private_key} {mon_eth_balance}\n'
        write_balance_result(text)

        await balance.client.session.close()


async def start_balance_checker(accounts):
    task = []
    for account in accounts:
        task.append(asyncio.create_task(start_checker(account)))

    await asyncio.gather(*task)
