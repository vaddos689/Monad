import asyncio

APRIORI_STAKE_RANGE = [0.0001, 0.0002] # MON selection range for staking
APRIORI_UNSTAKE_ALL = True
APRIORI_UNSTAKE_PRECENT = 50 # percent from all aprMON balance if APRIORI_UNSTAKE_ALL = False

AICRAFTREFCODE = '' # your aicraft refcode for sign-in
AICRAFT_VOTES_COUNT = 3 # number of votes per account

semaphore = asyncio.Semaphore(1) # number of simultaneously working accounts
