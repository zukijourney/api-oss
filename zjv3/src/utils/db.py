import json
import time
from aiofiles import open as aio_open
from asyncio import Lock
from fastapi import HTTPException
import traceback

data_file_lock = Lock()

async def load_data():
    async with data_file_lock:
        async with aio_open("data/db.json", mode="r") as file:
            return json.loads(await file.read())

async def save_data(data):
    async with data_file_lock:
        async with aio_open("data/db.json", mode="w") as file:
            await file.write(json.dumps(data, indent=4))

async def check_key_status(_, value, status):
    data = await load_data()
    return bool(next((item for item in data.values() if item.get("key") == value and item.get("status") == status), None))

async def key_check(key_type, value):
    return await check_key_status(key_type, value, "active")

async def ban_check(key_type, value):
    return not (await check_key_status(key_type, value, "active"))

async def premium_check(_, value):
    data = await load_data()
    return any(item.get("key") == value and item.get("premium") == "true" for item in data.values())

async def subscriber_check(_, value):
    data = await load_data()
    user_id = next((k for k, v in data.items() if v["key"] == value), None)
    current_time = time.time()
    if current_time >= data[user_id].get('subscriber_expiry', current_time): data[user_id]['subscribers'] = 'false'
    await save_data(data)
    return bool(next((item for item in data.values() if item.get("key") == value and item.get("subscribers", "false") == "true"), None))

async def ip_check(_, value, current_ip):
    user_data = await load_data()
    user_id = next((k for k, v in user_data.items() if v["key"] == value), None)
    if user_data[user_id]["ip"] is None:
        user_data[user_id]["ip"] = current_ip
        await save_data(user_data)
    elif user_data[user_id]["ip"] != current_ip:
        raise HTTPException(detail={"error": {"message": "IP does not match locked IP on record.", "type": "error", "tip": "Reset with /resetip at https://discord.gg/zukijourney", "param": None, "code": 403}}, status_code=403)
    
async def usage(value):
    user_data = await load_data()
    user_id = next((k for k, v in user_data.items() if v["key"] == value), None)
    user_data[user_id]["usage"] += 1
    await save_data(user_data)