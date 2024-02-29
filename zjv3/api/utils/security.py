from fastapi import Request, HTTPException
from ..database import DatabaseManager
from pyrate_limiter import Duration, Rate, Limiter, BucketFullException

limiter_rates = {
    "https://zukijourney.xyzbot.net/unf/chat/completions": Limiter([Rate(4, Duration.MINUTE)]),
    "https://zukijourney.xyzbot.net/v1/chat/completions": Limiter([Rate(12, Duration.MINUTE)]),
}

async def user_checks(request: Request):
    limiter_type = next((lim for lim in limiter_rates if lim in request.url.path), None)

    if not limiter_type:
        raise HTTPException(
            detail={"error": {"message": "Invalid URL. It should be https://zukijourney.xyzbot.net/v1 or /unf.", "type": "error", "param": None, "code": 400}},
            status_code=400
        )

    try:
        limiter_rates[limiter_type].try_acquire(request.headers.get("Authorization", "").replace("Bearer ", ""))
    except BucketFullException:
        raise HTTPException(
            detail={"error": {"message": "Too Many Requests.", "type": "error", "tip": "Just wait a little bit.", "param": None, "code": 429}},
            status_code=429
        )

    key = request.headers.get('Authorization', '').replace('Bearer ', '')

    if not key:
        raise HTTPException(
            detail={"error": {"message": "You didn't provide a key.", "type": "error", "param": None, "code": 401}},
            status_code=401
        )
    elif not await DatabaseManager.key_check(key):
        raise HTTPException(
            detail={"error": {"message": f"Your key '{key}' is invalid.", "type": "error", "param": None, "code": 402}},
            status_code=402
        )

    if not (await DatabaseManager.subscriber_check(key)):
        await DatabaseManager.ip_check(key, request.client.host)

    check_ban, check_credits = await DatabaseManager.ban_check(key), await DatabaseManager.credits_check(key)

    if check_ban:
        raise HTTPException(
            detail={"error": {"message": "Your key is banned.", "type": "error", "param": None, "code": 403}},
            status_code=403
        )
    elif not check_credits:
        raise HTTPException(
            detail={"error": {"message": "You've reached the credit limit.", "type": "error", "param": None, "code": 429}},
            status_code=429
        )

    await DatabaseManager.usage_update(key)