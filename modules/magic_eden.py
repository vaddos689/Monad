import asyncio
from loguru import logger
from utils_accs import write_result
from general_settings import semaphore
from general_settings import MAGIC_EDEN_CONTRACT
from config import MAGIC_EDEN_ABI
from modules.client import Client

class MagicEden:
    def __init__(self, account) -> None:
        self.account = account
        self.id = account['id']
        self.private_key = account['private_key']
        self.proxy = account['proxy']
        # Without Proxy (integrate only with blockchain)
        self.client = Client(self.id, self.private_key)
        
        self.magic_eden_contract = self.client.get_contract(MAGIC_EDEN_CONTRACT, MAGIC_EDEN_ABI)

    async def mint_nft(self):
        logger.info(f'[{self.id}] [{self.client.address}] mint ME nft contract: {MAGIC_EDEN_CONTRACT}')

        transaction = await self.magic_eden_contract.functions.mintPublic(
            self.client.address,
            0,
            1,
            "0x"
        ).build_transaction(await self.client.prepare_transaction())

        return await self.client.send_transaction(transaction, need_hash=True)


async def start_me(account):
    async with semaphore:
        magic_eden = MagicEden(account)

        logger.info(f'Start [{magic_eden.id}] account (stake)')
        tx_hash = await magic_eden.mint_nft()
        
        if tx_hash:
            result_text = f'{magic_eden.client.address} {magic_eden.private_key} MAGICEDEN_MINT {tx_hash.hex()}\n'
            write_result(result_text)

        await magic_eden.client.session.close()


async def start_magic_eden(accounts):
    task = []
    for account in accounts:
        task.append(asyncio.create_task(start_me(account)))

    await asyncio.gather(*task)
