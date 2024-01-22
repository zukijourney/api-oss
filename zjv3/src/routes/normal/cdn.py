from curl_cffi.requests import AsyncSession
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
import aiofiles
import json
import io

app = APIRouter()

@app.get("/v1/images/{image_uuid:str}.{ext:str}")
async def cdn(image_uuid: str, ext: str):
    try:
        async with aiofiles.open("data/images.json") as f:
            images = json.loads(await f.read())
    except:
        images = {}

    if not images.get(f"{image_uuid}.{ext}", None):
        return Response(content=json.dumps({
            "error": {
                "message": "Invalid image.",
                "type": "error",
                "tip": None,
                "param": None,
                "code": 400
            }
        }), status_code=400)

    async with AsyncSession(impersonate="chrome107") as session:
        try:
            r = await session.get(images.get(f"{image_uuid}.{ext}"))
            r.raise_for_status()
            image_content = r.content

        except Exception as e:
            return Response(content=json.dumps({
                "error": {
                    "message": str(e),
                    "type": "error",
                    "tip": "Troubleshoot at: https://discord.gg/zukijourney",
                    "param": None,
                    "code": 500
                }
            }), status_code=500)

    return StreamingResponse(io.BytesIO(image_content), media_type=f"image/png", status_code=200)