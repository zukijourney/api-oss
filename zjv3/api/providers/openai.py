import aiohttp
import random
import yaml

with open('data/providers/keys.yml') as f:
    keys = yaml.safe_load(f)['openai']

async def openai(body: dict):
    key = random.choice(keys)
    body.pop("stream", None)

    async with aiohttp.ClientSession() as session:
        headers = {"Authorization": f"Bearer {key}"}
        async with session.get("https://api.openai.com/v1/chat/completions", headers=headers, json=body) as resp:
            return (await resp.json())['choices'][0]['message']['content']