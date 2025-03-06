import asyncio

APRIORI_STAKE_RANGE = [0.0001, 0.0002] # MON selection range for staking

AICRAFTREFCODE = '' # your aicraft refcode for sign-in
AICRAFT_VOTES_COUNT = 1 # number of votes per account

semaphore = asyncio.Semaphore(1) # number of simultaneously working accounts
