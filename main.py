import asyncio
from loguru import logger

from utils_accs import get_accounts
from modules.apriori import start_accounts_for_apriori
from modules.aicraft import start_accounts_for_aicraft

async def start(module: str):
    accounts = get_accounts()
    logger.info(f'Загрузил {len(accounts)} аккаунтов')

    if module == 'apriori':
        logger.info('Start Apriori module')
        await start_accounts_for_apriori(accounts)

    if module == 'aicraft':
        logger.info('Start AIcraft module')
        await start_accounts_for_aicraft(accounts)


if __name__ == '__main__':
    action = int(input('\n1. Apriori Stake'
                        '\n2. AIcraft vote'
                        '\nSelect module: '))
    if action == 1:
        asyncio.run(start('apriori'))
    if action == 2:
        asyncio.run(start('aicraft'))