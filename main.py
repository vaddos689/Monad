import asyncio
from loguru import logger

from utils_accs import get_accounts
from modules.apriori import start_accounts_for_apriori
from modules.aicraft import start_accounts_for_aicraft
from modules.balance import start_balance_checker

async def start(module: str):
    accounts = get_accounts()
    logger.info(f'Загрузил {len(accounts)} аккаунтов')

    if module == 'apriori_stake':
        logger.info('Start Apriori stake module')
        await start_accounts_for_apriori(accounts, 'stake')

    if module == 'apriori_unstake':
        logger.info('Start Apriori unstake module')
        await start_accounts_for_apriori(accounts, 'unstake')

    if module == 'aicraft':
        logger.info('Start AIcraft module')
        await start_accounts_for_aicraft(accounts)
    
    if module == 'balance_checker':
        logger.info('Start Balance checker module')
        await start_balance_checker(accounts)
        logger.info("Balance checker result in: balance_checker_result.txt")
    

if __name__ == '__main__':
    action = int(input('\n1. Apriori Stake'
                        '\n2. AIcraft vote'
                        '\n3. Balance checker'
                        '\nSelect module: '))
    if action == 1:
        apriori_action = int(input('\n1. Stake MON'
                                   '\n2. Unstake MON'
                                   '\nSelect Apriori action: '))
        if apriori_action == 1:
            asyncio.run(start('apriori_stake'))

        if apriori_action == 2:
            asyncio.run(start('apriori_unstake'))

    if action == 2:
        asyncio.run(start('aicraft'))

    if action == 3:
        asyncio.run(start('balance_checker'))