import asyncio
import random
from loguru import logger
from utils_accs import write_result
from general_settings import semaphore, APRIORI_STAKE_RANGE, APRIORI_UNSTAKE_ALL, APRIORI_UNSTAKE_PRECENT
from config import APRIORI_ABI, APRIORI_CONTRACT
from modules.client import Client
from decimal import Decimal, ROUND_FLOOR

def get_random_float_from_range(range_: list):
    return round(random.uniform(range_[0], range_[1]), 4)

class Apriori:
    def __init__(self, account) -> None:
        self.account = account
        self.id = account['id']
        self.private_key = account['private_key']
        self.proxy = account['proxy']
        # Without Proxy (integrate only with blockchain)
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

        return await self.client.send_transaction(transaction, need_hash=True)

    def round_to_min_step(self, value, min_value=0.0001):
        d = Decimal(str(value)).quantize(Decimal('0.0001'), rounding=ROUND_FLOOR)
        return max(d, Decimal(str(min_value)))

    async def unstake_mon(self):
        aprMON_balance_in_wei, aprMON_balance, _ = await self.client.get_token_balance('aprMON')
        
        logger.info(f'[{self.id}] [{self.client.address}] aprMON balance: {aprMON_balance} MON')
        
        if APRIORI_UNSTAKE_ALL:
            unstake_amount_mon = aprMON_balance
            rounded_amount_mon = self.round_to_min_step(unstake_amount_mon)
            shares = int(rounded_amount_mon * 10**18)
            logger.info(f'[{self.id}] [{self.client.address}] unstake all {self.client.w3.from_wei(shares, 'ether')} aprMON')
        else:
            unstake_amount_mon = (APRIORI_UNSTAKE_PRECENT / 100) * aprMON_balance
            rounded_amount_mon = self.round_to_min_step(unstake_amount_mon)
            shares = int(rounded_amount_mon * 10**18)
            logger.info(f'[{self.id}] [{self.client.address}] unstake {APRIORI_UNSTAKE_PRECENT}% aprMON == {self.client.w3.from_wei(shares, 'ether')}')        
        
        transaction = await self.apriori_contract.functions.requestRedeem(
            shares,
            self.client.address,
            self.client.address
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction, need_hash=True)


async def start_apriori(account, action):
    async with semaphore:

        apriori = Apriori(account)

        if action == 'stake':
            logger.info(f'Start [{apriori.id}] account (stake)')
            tx_hash = await apriori.stake_mon()
            
            if tx_hash:
                result_text = f'{apriori.client.address} {apriori.private_key} APRIORI_STAKE {tx_hash.hex()}'
                write_result(result_text)

            await apriori.client.session.close()

        if action == 'unstake':
            logger.info(f'Start [{apriori.id}] account (unstake)')
            tx_hash = await apriori.unstake_mon()

            if tx_hash:
                result_text = f'{apriori.client.address} {apriori.private_key} APRIORI_UNSTAKE {tx_hash.hex()}'
                write_result(result_text)

            await apriori.client.session.close()


async def start_accounts_for_apriori(accounts, action):
    task = []
    for account in accounts:
        task.append(asyncio.create_task(start_apriori(account, action)))

    await asyncio.gather(*task)
