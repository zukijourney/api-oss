import ujson
import aiofiles
import uuid
import time
from typing import Optional, Any
from pydantic import BaseModel, field_validator
from fastapi import APIRouter, Depends, Request, HTTPException
from curl_cffi.requests import AsyncSession
from ...utils.security import user_checks
from ...providers.openai import openai
from ...database import DatabaseManager
from ...utils import helpers

app = APIRouter()

models = [
    "kandinsky-2.2", "sdxl", "latent-consistency-model",
    "pollinations", "realvisxl-v3", "opendalle", "dall-e-3", 
    "pixart-xl-2", "sdxl-turbo", "playground-v2", "midjourney"
    "pastel-mix-anime", "absolute-reality-v1.6", "anything-v5"
    "meinamix", "deliberate", "rev-animated", "dreamshaper-8"
    "realistic-vision-v5", "openjourney-v4", "absolute-reality-v1.8.1",
    "absolute-reality-v1.6", "anything-v3", "anything-v4.5",
    "dreamshaper-6", "dreamshaper-7", "kandinsky-3", "deliberate-v2"
    "realistic-vision-v4", "realistic-vision-v1.4", "realistic-vision-v2"
]

class ImagesBody(BaseModel):
    prompt: Any
    model: Any
    n: Optional[int] = 1
    size: Optional[str] = '1024x1024'

    @classmethod
    def model_check(cls, model):
        if not isinstance(model, str) or model not in models:
            raise ValueError('Invalid model.')
    
    @classmethod
    def prompt_check(cls, prompt):
        if not isinstance(prompt, str):
            raise ValueError('Invalid prompt.')

    @field_validator("model")
    def validate_model(cls, v):
        cls.model_check(v)
        return v

    @field_validator("prompt")
    def validate_prompt(cls, v):
        cls.prompt_check(v)
        return v

async def load_images():
    async with aiofiles.open("data/images/list.json") as f:
        try:
            data = await f.read()
            return ujson.loads(data)
        except:
            return {}

async def save_images(data):
    async with aiofiles.open("data/images/list.json", "w") as f:
        await f.write(ujson.dumps(data, indent=4))

@app.post("/v1/images/generations", dependencies=[Depends(user_checks)])
async def images(request: Request, data: ImagesBody) -> None:
    prompt, model, key = data.prompt, data.model, request.headers.get("Authorization", "").replace("Bearer ", "")

    if not (await DatabaseManager.premium_check(key)) and model == "midjourney":
       raise HTTPException(detail={"error": {"message": f"You don't have access to '{model}'.", "type": "error", "param": None, "code": 400}}, status_code=400)
    
    url = await openai(model, prompt)

    if not url or url == "":
        raise HTTPException(detail={"error": {"message": f"The provider for {model} sent an invalid response.", "type": "error", "param": None, "code": 500}}, status_code=500)
    
    async with AsyncSession(impersonate="chrome107") as session:
        r = await session.get(url)
        content_type = r.headers.get("Content-Type", "")

        if not content_type.startswith("image/"):
            raise HTTPException(detail={"error": {"message": "The content returned was not an image.", "type": "error", "param": None, "code": 500}}, status_code=500)

        image_dict, image_uuid = await load_images(), f"{str(uuid.uuid4())}"
        image_dict[image_uuid] = url
        await save_images(image_dict)

    helpers.create_background_task(DatabaseManager.credits_update(key, 150 if model != "midjourney" else 2500))

    return {"created": int(time.time()), "data": [{"url": f"https://zukijourney.xyzbot.net/cdn/{image_uuid}"}]}