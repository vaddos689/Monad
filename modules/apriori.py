import asyncio
import random
from loguru import logger
from utils_accs import write_result
from general_settings import semaphore, APRIORI_STAKE_RANGE
from config import APRIORI_ABI, APRIORI_CONTRACT
from modules.client import Client

def get_random_float_from_range(range_: list):
    return round(random.uniform(range_[0], range_[1]), 4)

class Apriori:
    def __init__(self, account) -> None:
        self.account = account
        self.id = account['id']
        self.private_key = account['private_key']
        self.proxy = account['proxy']
        # Без прокси, только транзы
        self.client = Client(self.id, self.private_key)
        self.apriori_contract = self.client.get_contract(APRIORI_CONTRACT, APRIORI_ABI)

    async def stake_mon(self):
        random_stake_amount = get_random_float_from_range(APRIORI_STAKE_RANGE)
        logger.info(f'[{self.id}] [{self.client.address}] random stake amount MON: {random_stake_amount}')
        
        wallet_balance_in_wei, wallet_balance, _ = await self.client.get_token_balance(check_native=True)
        
        logger.info(f'[{self.id}] [{self.client.address}] Wallet balance MON: {wallet_balance}')
        if wallet_balance < random_stake_amount:
            logger.info(f'[{self.id}] [{self.client.address}] wallet balance < stake amount. skip')
            return
        
        random_stake_amount_wei = int(random_stake_amount * 10 ** 18)
        transaction = await self.apriori_contract.functions.deposit(
            random_stake_amount_wei,
            self.client.address
        ).build_transaction(await self.client.prepare_transaction(value=random_stake_amount_wei))

        return await self.client.send_transaction(transaction)


async def start_apriori(account):
    async with semaphore:
        apriori = Apriori(account)
        logger.info(f'Start [{apriori.id}] account')
        tx_hash = await apriori.stake_mon()
        if tx_hash:
            result_text = f'{apriori.client.address} {apriori.proxy} APRIORI_STAKE {tx_hash.hex()}'
            write_result(result_text)
        await apriori.client.session.close()


async def start_accounts_for_apriori(accounts):
    task = []
    for account in accounts:
        task.append(asyncio.create_task(start_apriori(account)))

    await asyncio.gather(*task)
