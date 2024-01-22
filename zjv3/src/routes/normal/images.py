import json
import traceback
import aiofiles
import uuid
import httpx
from fastapi import Response, APIRouter, Depends, Body, Request
from curl_cffi.requests import AsyncSession
from ...utils.security import security
from ...utils.db import premium_check

app = APIRouter()

models = [
    "kandinsky-2.2", "sdxl", "latent-consistency-model", "playground-v2",
    "midjourney", "pollinations", "realvisxl-v3", "opendalle", 
    "dall-e-3","pixart-xl-2", "sdxl-turbo", "sdxl-unfiltered", 
    "sdxl-unfiltered-anime", "sdxl-unfiltered-realistic"
]

async def upload_image(data):
    url, params = "https://api.imgbb.com/1/upload", {"expiration": 600, "key": ""}
    files = {"image": data}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, params=params, files=files)

    return response.json()['data']['url']

async def load_images():
    try:
        async with aiofiles.open("data/images.json") as f:
            return json.loads(await f.read())
    except:
        return {}

async def save_images(data):
    async with aiofiles.open("data/images.json", "w") as f:
        await f.write(json.dumps(data))

@app.post("/v1/images/generations", dependencies=[Depends(security)])
async def images(request: Request, data: dict = Body(...)) -> None:
    try:
        prompt, model, neg_prompt, width, height, key = data.get("prompt"), data.get("model"), data.get("negative_prompt", ""), data.get("width", None), data.get("height", None), request.headers.get("Authorization", None)
        
        if model not in models or prompt is None or not isinstance(model, str) or not isinstance(prompt, str):
            return Response(content=json.dumps({"error": {"message": "Invalid model or prompt.", "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 400}}), status_code=400)
        
        if not (await premium_check("api_key", key.replace("Bearer ", ""))) and model == "dall-e-3":
            return Response(content=json.dumps({"error": {"message": f"You don't have access to '{model}'.", "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 400}}), status_code=400)
            
        if width and height:
            if width > 2048 or height > 2048 or width % 8 != 0 or height % 8 != 0:
                return Response(content=json.dumps({"error": {"message": "Input width/height must be within 8-2048, and divisible by 8.", "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 400}}), status_code=400)
            load = [neg_prompt, width, height]
        else:
            load = ["", 1024, 1024]
        
        url = "example.com"
            
        if url is None or url == "":
            return Response(content=json.dumps({"error": {"message": "The provider sent an invalid response.", "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 500}}), status_code=500)

        async with AsyncSession(impersonate="chrome107") as session:
            r = await session.get(url)
            content_type, image_extension = r.headers.get("Content-Type", ""), content_type.split("/")[-1] if content_type else None

            if not content_type.startswith("image/"):
                return Response(content=json.dumps({"error": {"message": "The content returned was not an image.", "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 500}}), status_code=500)
            
            image_directory, image_uuid = await load_images(), f"{str(uuid.uuid4())}.{image_extension}"
            image_directory[image_uuid] = url
            await save_images(image_directory)
            
        return Response(json.dumps({"data": [{"url": f"https://zukijourney.xyzbot.net/v1/images/{image_uuid}"}]}), media_type="application/json", status_code=200)
    except Exception as e:
        print(traceback.format_exc())
        return Response(content=json.dumps({"error": {"message": str(e), "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 500}}), status_code=500)