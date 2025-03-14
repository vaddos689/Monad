import asyncio

APRIORI_STAKE_RANGE = [0.005, 0.1] # MON selection range for staking
APRIORI_UNSTAKE_ALL = True
APRIORI_UNSTAKE_PRECENT = 50 # percent from all aprMON balance if APRIORI_UNSTAKE_ALL = False

AICRAFTREFCODE = '' # your aicraft refcode for sign-in
AICRAFT_VOTES_COUNT = 5 # number of votes per account

KINTSU_STAKE_RANGE = [0.01, 0.0112] # !!! MINIMUM 0.01 !!! MON selection range for staking
KINTSU_UNSTAKE_ALL = True
KINTSU_UNSTAKE_PRECENT = 50 # percent from all aprMON balance if APRIORI_UNSTAKE_ALL = False

semaphore = asyncio.Semaphore(1) # number of simultaneously working accounts