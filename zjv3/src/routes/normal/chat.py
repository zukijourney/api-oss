import json
import random
import string
import time
import asyncio
import traceback
from aiofiles import open as aio_open
from fastapi import Request, Response, APIRouter, Depends, Body
from fastapi.responses import StreamingResponse
from ...providers.openai import ai as openai
from ...utils.security import security
from ...utils.db import premium_check

app = APIRouter()

data_file_lock = asyncio.Lock()

normal_models = [
    "gpt-3.5-turbo", "gpt-3.5-turbo-instruct", "gpt-3.5-turbo-16k", "gpt-4",
    "claude-instant-v1", "mixtral-8x7b-instruct", "mistral-medium", "mistral-7b-instruct",
    "codellama-7b-instruct", "llama-2-7b", "llama-2-13b", "llama-2-70b", "gemini-pro",
    "gemini-pro-vision", "palm-2", "sheep-duck-llama", "goliath-120b", "yi-34b",
    "solar10-7b", "openchat", "unfiltered-maxi", "unfiltered-mini"
]

premium_models = [
    "gpt-4-1106-preview", "gpt-4-vision-preview", "claude-2", "claude-2.1",
    "claude", "claude-instant-v1-100k"
]

rp_websites = [
    "https://venus.chub.ai/", "https://www.janitorai.com/", "https://janitorai.chat/",
    "https://janitorai.pro/", "https://risuai.xyz/", "https://venuschat.ai/",
    "https://venuschat.ai", "https://risuai.xyz", "https://janitorai.chat/",
    "https://janitorai.pro", "https://venus.chub.ai", "https://www.janitorai.com",
]


def combine_messages(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    combined_message = "\n\n".join(
        f"{msg['role'].capitalize()}: {msg['content']}" for msg in messages
    )
    return [{"role": "user", "content": combined_message}]

async def generate_completion_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))

async def generate_timestamp():
    return int(time.time())

async def streaming(text, completion_id, completion_timestamp, model):
    try:
        for chunk in text:
            content = create_completion_data(chunk, completion_id,
                                             completion_timestamp, model)
            yield f"data: {content}\n\n"
            await asyncio.sleep(0.005)

        content = create_end_completion_data(completion_id, completion_timestamp,
                                             model)
        yield f"data: {content}\n\n"

    except GeneratorExit:
        pass

def create_completion_data(chunk: str, completion_id: str,
                           completion_timestamp: int, model: str):
    return json.dumps(
        {
            "id":
                f"chatcmpl-{completion_id}",
            "object":
                "chat.completion.chunk",
            "created":
                completion_timestamp,
            "model":
                model,
            "choices": [{
                "index": 0,
                "delta": {
                    "content": chunk
                },
                "finish_reason": None
            }]
        },
        separators=(",", ":"))

def create_end_completion_data(completion_id: str, completion_timestamp: int,
                               model: str):
    return json.dumps(
        {
            "id": f"chatcmpl-{completion_id}",
            "object": "chat.completion.chunk",
            "created": completion_timestamp,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        },
        separators=(",", ":"))

async def load_data():
    async with data_file_lock:
        async with aio_open("data/db.json", mode="r") as file:
            return json.loads(await file.read())

async def save_data(data):
    async with data_file_lock:
        async with aio_open("data/db.json", mode="w") as file:
            await file.write(json.dumps(data, indent=4))

def downgrade_condition(messages: list[str], model: str) -> bool:
    return ((len(messages[-1]["content"]) < 40 and "gpt-4" not in model) or (
        len(messages[-1]["content"]) < 30 and "gpt-4" in model 
    )) and len(str(messages)) < 1000

@app.post("/chat/completions", dependencies=[Depends(security)])
@app.post("/v1/v1/chat/completions", dependencies=[Depends(security)])
@app.post("/v1/chat/completions/chat/completions", dependencies=[Depends(security)])
@app.post("/v1/chat/completions/v1/chat/completions", dependencies=[Depends(security)])
@app.post("/v1/chat/completions", dependencies=[Depends(security)])
async def chat(request: Request, data: dict = Body(...)) -> None:
    try:
        messages, model, stream, key, origin = data.get("messages", None), data.get("model", "penis"), data.get("stream", False) or data.get("streaming", False), request.headers.get("Authorization", None), request.headers.get("Referer", "") or request.headers.get("Http-Referer", "") or request.headers.get("Origin", "")

        if model not in normal_models and model not in premium_models or messages is None:
            return Response(content=json.dumps({"error": {"message": "Invalid model or messages.", "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 400}}), status_code=400)
        
        premium = await premium_check("key", key.replace("Bearer ", ""))
        if not premium and model in premium_models:
            return Response(content=json.dumps({"error": {"message": "You don't have access to this model.", "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 400}}), status_code=400)
        
        flagged = False
        for b in banned_content:
            if b in str(messages).lower():
                flagged = True
                break
        
        if (origin in rp_websites or flagged) and not "poop" in key:
            datuh = await load_data()
            user_id = next((k for k, v in data.items() if v["key"] == key), None)
            datuh[user_id]["status"] = "rp-not-allowed-here"
            await save_data(datuh)
            return Response(content=json.dumps({"error": {"message": "No RP for you here, bitch. Goon to child porn elsewhere.", "type": "error", "tip": "Go outside.", "param": None, "code": 403}}), status_code=403)
        
        content = await openai(data)
        
        if content is None or content == "":
            return Response(content=json.dumps({"error": {"message": "The provider sent an invalid response.", "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 500}}), status_code=500)

        completion_id, completion_timestamp = await generate_completion_id(), await generate_timestamp()

        if stream:
            return StreamingResponse(content=streaming(content, completion_id, completion_timestamp, model), media_type="text/event-stream", status_code=200)
        else:
            return {
                "id": f"chatcmpl-{completion_id}",
                "object": "chat.completion",
                "created": completion_timestamp,
                "model": model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }

    except Exception as e:
        print(traceback.format_exc())
        return Response(content=json.dumps({"error": {"message": str(e), "type": "error", "tip": "Troubleshoot at: https://discord.gg/zukijourney", "param": None, "code": 500}}), status_code=500)