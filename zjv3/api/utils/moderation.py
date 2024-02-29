import aiocache
from .helpers import stringify_messages

cache = aiocache.Cache(aiocache.SimpleMemoryCache)

with open('data/moderation/wordlist.txt', 'r') as f:
    list_of_words = f.read().splitlines()

async def moderation(inp):
    inp = await stringify_messages(inp)

    if await cache.exists(inp):
        return await cache.get(inp)
    else:
        await cache.set(inp, await check_nsfw(inp))
        return await cache.get(inp)

async def check_nsfw(inp):
    profanity_hits = []
    for word in list_of_words:
        if word in inp:
            profanity_hits.append(word)
    return len(profanity_hits) <= 4