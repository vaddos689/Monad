import asyncio
import random
from loguru import logger
from utils_accs import write_result
from eth_account.messages import encode_defunct
from eth_account import Account

from general_settings import semaphore, AICRAFTREFCODE, AICRAFT_VOTES_COUNT
from config import AICRAFT_CONTRACT, AICRAFT_DATA, AICRAFT_ABI
from modules.client import Client

def get_random_vote_params():
    random_item = random.choice(list(AICRAFT_DATA.items()))
    name, id_value = random_item
    return {"id": id_value, "name": name}

class AIcraft:
    def __init__(self, account) -> None:
        self.account = account
        self.id = account['id']
        self.private_key = account['private_key']
        self.proxy = account['proxy']

        self.client = Client(self.id, self.private_key, self.proxy)
        self.aicraft_contract = self.client.get_contract(AICRAFT_CONTRACT, AICRAFT_ABI)
        self.account_eth = Account().from_key(self.private_key)

    async def get_message(self):
        url = f'https://api.aicraft.fun/auths/wallets/sign-in/message?address={self.client.address}&type=ETHEREUM_BASED'
        response = await self.client.session.get(url)
        r = await response.json()
        if r['statusCode'] == 200:
            return r['data']['message']
        else:
            logger.error(f'[{self.id}] [{self.client.address}] Error with get message for auth: {r}')
            return None

    async def sign_message(self, message: str):
        encoded_message = encode_defunct(text=message)
    
        signed_message = self.client.w3.eth.account.sign_message(
            encoded_message,
            private_key=self.client.private_key
        )
        
        return signed_message
    
    async def get_auth_token(self, message, signed_message):
        url = 'https://api.aicraft.fun/auths/wallets/sign-in'
        payload = {
            'address': self.client.address, 
            'message': message,
            'refCode': AICRAFTREFCODE,
            'signature': signed_message,
            'type': 'ETHEREUM_BASED'
        }
        response = await self.client.session.post(url, data=payload)
        r = await response.json()
        if r['statusCode'] == 201:
            return r['data']['token']
        else:
            logger.error(f'[{self.id}] [{self.client.address}] Error with sign-in: {r}')
            return None

    async def me(self):
        url = 'https://api.aicraft.fun/users/me?includeTodayFeedCount=true'
        response = await self.client.session.get(url)
        r = await response.json()
        if r['statusCode'] == 200:
            for wallet in r['data']['wallets']:
                if self.client.w3.to_checksum_address(wallet['address']) == self.client.address:
                    _id = wallet['_id']
                    return _id, r['data']['invitedBy']['refCode'], r['data']['todayFeedCount']
                
    async def confirm(self, request_id, ref_code, tx_hash):
        url = f'https://api.aicraft.fun/feeds/orders/{request_id}/confirm'
        payload = {
            'refCode': ref_code,
            'transactionHash': tx_hash
        }
        response = await self.client.session.post(url, data=payload)
        r = await response.json()
        if r['statusCode'] == 201:
            return True
    
    async def orders(self, vote_id, walletID, invited_by_REFCODE):
        url = 'https://api.aicraft.fun/feeds/orders'
        payload = {
            'candidateID': vote_id,
            'chainID': '10143',
            'feedAmount': 1,
            'refCode': invited_by_REFCODE,
            'walletID': walletID
        }
        response = await self.client.session.post(url, json=payload)
        r = await response.json()
        if r['statusCode'] == 201:
            return r
        else:
            logger.error(f'[{self.id}] [{self.client.address}] Error with get orders: {r}')
            return None
    
    async def random_vote(self):
        message = await self.get_message()
        if message == None:
            return
        signed_message = (await self.sign_message(message)).signature.hex()
        auth_token = await self.get_auth_token(message, signed_message)
        if auth_token == None:
            return
        logger.info(f'[{self.id}] [{self.client.address}] success auth on AIcraft')

        self.client.session.headers.add('Accept', 'application/json')
        self.client.session.headers.add('Authorization', f'Bearer {auth_token}')

        for i in range(AICRAFT_VOTES_COUNT):
            wallet_id, invited_by_REFCODE, today_votes = await self.me()

            random_vote = get_random_vote_params()
        
            orders = await self.orders(random_vote['id'], wallet_id, invited_by_REFCODE)
            if orders == None:
                return
            
            logger.info(f'[{self.id}] [{self.client.address}] random AIcraft vote: {random_vote['name']}')

            wallet_balance_in_wei, wallet_balance, _ = await self.client.get_token_balance(check_native=True)
            
            logger.info(f'[{self.id}] [{self.client.address}] Wallet balance MON: {wallet_balance}')
            if wallet_balance == 0:
                logger.info(f'[{self.id}] [{self.client.address}] wallet balance 0 MON')
                return
            
            orders_params = orders['data']['payment']['params']

            _candidateID = orders_params['candidateID']
            _feedAmount = orders_params['feedAmount']
            _requestID = orders_params['requestID']
            _requestData = orders_params['requestData']

            message_hash = orders_params['userHashedMessage']
            message = encode_defunct(hexstr=message_hash)
            signature = self.account_eth.sign_message(message)
            user_signature = signature.signature.hex()

            _integritySignature = orders_params['integritySignature']

            transaction = await self.aicraft_contract.functions.feed(
                _candidateID,
                _feedAmount,
                _requestID,
                _requestData,
                bytes.fromhex(user_signature[2:]),
                bytes.fromhex(_integritySignature[2:])
            ).build_transaction(await self.client.prepare_transaction())

            tx_hash = await self.client.send_transaction(transaction, need_hash=True)
            if tx_hash:
                confirm = await self.confirm(_requestID, invited_by_REFCODE, tx_hash.hex())
                if confirm:
                    result_text = f'{self.client.address} {self.proxy} AICRAFT_VOTE {tx_hash.hex()}\n'
                    write_result(result_text)
        logger.info(f'[{self.client.account_id}] [{self.client.address}] Finish AIcraft task')


async def start_aicraft(account):
    async with semaphore:
        aicraft = AIcraft(account)
        logger.info(f'Start [{aicraft.id}] account')
        await aicraft.random_vote()
        await aicraft.client.session.close()


async def start_accounts_for_aicraft(accounts):
    task = []
    for account in accounts:
        task.append(asyncio.create_task(start_aicraft(account)))

    await asyncio.gather(*task)
