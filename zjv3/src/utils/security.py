from fastapi import Request
from fastapi.exceptions import HTTPException
from pyrate_limiter import Duration, Rate, Limiter, BucketFullException
from ..utils.db import key_check, ban_check, premium_check, subscriber_check, ip_check, usage

normal_limiter = Limiter([Rate(3, Duration.MINUTE), Rate(200, Duration.DAY)])
premium_limiter = Limiter([Rate(7, Duration.MINUTE), Rate(789, Duration.DAY)])
subscriber_limiter = Limiter(Rate(11, Duration.MINUTE))

async def security(request: Request):
    authorization = request.headers.get("Authorization", None)
    
    if not authorization:
        raise HTTPException(detail={"error": {"message": "You didn't provide a key.", "type": "error", "tip": "Get your key at: https://discord.gg/zukijourney", "param": None, "code": 401}}, status_code=401)
    
    if authorization.replace("Bearer ", "").startswith('zp-'):
        raise HTTPException(detail={"error": {"message": "The 'zp-' key prefix is now discontinued.", "type": "error", "tip": "Regenerate or get your key at: https://discord.gg/zukijourney", "param": None, "code": 401}}, status_code=401)
    
    if not (await key_check("key", authorization.replace("Bearer ", ""))):
        raise HTTPException(detail={"error": {"message": "Your key is invalid.", "type": "error", "tip": "Get your key at: https://discord.gg/zukijourney", "param": None, "code": 401}}, status_code=401)

    if await ban_check("key", authorization.replace("Bearer ", "")):
        raise HTTPException(detail={"error": {"message": "Your key is banned.", "type": "error", "tip": "Appeal your ban at: https://discord.gg/zukijourney", "param": None, "code": 403}}, status_code=403)
    
    await ip_check("api_key", authorization.replace("Bearer ", ""), request.client.host)
    limiter = normal_limiter if not await premium_check("key", authorization.replace("Bearer ", "")) else premium_limiter if not await subscriber_check("key", authorization.replace("Bearer ", "")) else subscriber_limiter
    await usage(authorization.replace("Bearer ", ""))
    try:
        limiter.try_acquire(authorization)
    except BucketFullException:
        raise HTTPException(detail={"error": {"message": "Too Many Requests.", "type": "error", "tip": "Just wait a little bit.", "param": None, "code": 429}}, status_code=429)