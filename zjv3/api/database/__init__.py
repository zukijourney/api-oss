import yaml
import time
import ujson
import random
import string
from redis.asyncio import Redis
from fastapi import HTTPException

with open("data/credits.yml") as f:
    credits_list = yaml.safe_load(f)

with open("secrets/values.yml") as f:
    config = yaml.safe_load(f)

class DatabaseManager:
    _redis = Redis.from_url(url=config['redis']['url'])

    @staticmethod
    async def _load_db():
        try:
            return ujson.loads(await DatabaseManager._redis.get("keys"))
        except:
            return {}

    @staticmethod
    async def _save_db(data: dict):
        await DatabaseManager._redis.set("keys", ujson.dumps(data))
    
    @staticmethod
    async def _check_data_key_value_status(value: str, status: str):
        return any(item[0].get("key") == value and item[0].get("status") != status for item in (await DatabaseManager._load_db()).values())
    
    @staticmethod
    async def delete_account(value: str):
        data = await DatabaseManager._load_db()  
        get_key = next((v for _, v in data.items() if v[0].get("key") == value), None)
        get_key[0] = {}
        await DatabaseManager._save_db(data)
    
    @staticmethod
    async def create_account(value: str):
        data = await DatabaseManager._load_db()
        key = f"zu-{''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))}"
        data[value] = [{"key": key, "status": "active", "banned": "false", "premium": "false", "ip": None, "credits": str(credits_list['credits']['normal'] * 250), "credits_last_reset": int(time.time())}]
        await DatabaseManager._save_db(data)
        return key
    
    @staticmethod
    async def key_check(value: str):
        data = await DatabaseManager._load_db()
        key = next((v for _, v in data.items() if v[0].get("key") == value), None)
        return key[0].get("key") if key else None

    @staticmethod
    async def ban_check(value: str):
        return await DatabaseManager._check_data_key_value_status(value, "active")

    @staticmethod
    async def premium_check(value: str):
        return any(item[0].get("key") == value and item[0].get("premium") == "true" for item in (await DatabaseManager._load_db()).values())

    @staticmethod
    async def subscriber_check(value: str):
        return any((item[0].get("key") == value and item[0].get("subscribers") == "true" and int(item[0].get("subscriber_expiry", 0)) > int(time.time())) for item in (await DatabaseManager._load_db()).values())

    @staticmethod
    async def ip_check(value: str, ip: str):
        data = await DatabaseManager._load_db()
        key = next((v for _, v in data.items() if v[0].get("key") == value), None)

        if (key[0]["ip"] and key[0]["ip"] != ip):
            raise HTTPException(
                detail={
                    "error": {
                        "message": "The IP does not match the key's locked IP in the database.",
                        "type": "error",
                        "param": None,
                        "code": 403
                    }
                },
                status_code=403,
            )
        elif not key[0]["ip"]:
            key[0]["ip"] = ip
            await DatabaseManager._save_db(data)

        return True

    @staticmethod
    async def credits_check(value: str):
        data = await DatabaseManager._load_db()
        key = next((v for _, v in data.items() if v[0].get("key") == value), None)
        return int(key[0]['credits']) > 0

    @staticmethod
    async def credits_update(value: str, tokens: int, set_tokens: bool = False):
        data = await DatabaseManager._load_db()
        key = next((v for _, v in data.items() if v[0].get("key") == value), None)
        key[0]['credits'] = f"{int(key[0].get('credits', 0)) - tokens}" if not set_tokens else str(tokens)
        key[0]['credits_last_reset'] = str(int(time.time()))
        await DatabaseManager._save_db(data)
    
    @staticmethod
    async def usage_update(value: str):
        data = await DatabaseManager._load_db()
        key = next((v for _, v in data.items() if v[0].get("key") == value), None)
        key[0]['usage'] = f"{int(key[0].get('usage', 0)) + 1}"
        await DatabaseManager._save_db(data)
    
    @staticmethod
    async def ban_update(value: str, ban: bool):
        data = await DatabaseManager._load_db()
        key = next((v for _, v in data.items() if v[0].get("key") == value), None)
        key[0]['status'] = "disabled" if ban else "active"
        await DatabaseManager._save_db(data)
    
    @staticmethod
    async def premium_update(value: str, premium: bool):
        data = await DatabaseManager._load_db()
        key = next((v for _, v in data.items() if v[0].get("key") == value), None)
        key[0]['premium'] = "true" if premium else "false"
        await DatabaseManager._save_db(data)
    
    @staticmethod
    async def subscriber_update(value: str, subscriber: bool):
        data = await DatabaseManager._load_db()
        key = next((v for _, v in data.items() if v[0].get("key") == value), None)
        key[0]['subscribers'] = "true" if subscriber else "false"
        key[0]['subscriber_expiry'] = str((int(time.time()) + 2629800)) if subscriber else "0"
        key[0]['credits'] = str(int(credits_list['credits']['subscriber']) * 250)
        await DatabaseManager._save_db(data)