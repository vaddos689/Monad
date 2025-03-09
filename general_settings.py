import asyncio

APRIORI_STAKE_RANGE = [0.0001, 0.0002] # MON selection range for staking
APRIORI_UNSTAKE_ALL = True
APRIORI_UNSTAKE_PRECENT = 50 # percent from all aprMON balance if APRIORI_UNSTAKE_ALL = False

AICRAFTREFCODE = '' # your aicraft refcode for sign-in
AICRAFT_VOTES_COUNT = 3 # number of votes per account

MAGIC_EDEN_CONTRACT = '0xa951bb8126d81d6aeaf73cc335fc7b7444df9520'

semaphore = asyncio.Semaphore(1) # number of simultaneously working accounts