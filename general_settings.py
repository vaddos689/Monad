import asyncio

APRIORI_STAKE_RANGE = [0.0001, 0.0002]

AICRAFTREFCODE = ''
AICRAFT_VOTES_COUNT = 1 # Сколько раз голосовать

semaphore = asyncio.Semaphore(1) # Кол-во одновременно работаюших аккаунтов
