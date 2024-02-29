import ujson
import random
import string
import time
import asyncio
from typing import Optional, Any
from pydantic import BaseModel, field_validator
from fastapi import Request, APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from ...utils.security import user_checks
from ...database import DatabaseManager
from ...utils import helpers
from ...providers import openai

app = APIRouter()

models = [
    "gpt-3.5-turbo-0301",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-instruct",
    "gpt-3.5-turbo-16k-0613",
    "gpt-3.5-turbo-16k",
    "claude-instant-v1",
    "mixtral-8x7b-instruct",
    "mistral-tiny",
    "mistral-small",
    "mistral-medium",
    "gpt-4",
    "gpt-4-0613",
    "gpt-4-0314",
    "mistral-7b-instruct",
    "codellama-7b-instruct",
    "llama-2-7b",
    "llama-2-13b",
    "llama-2-70b",
    "gemini-pro",
    "palm-2",
    "yi-34b",
    "openchat",
    "pi",
    "mythomist-7b",
    "mythomax-l2-13b",
    "cinematika-7b",
    "gemma-7b"
]

premium_models = [
    "claude",
    "claude-1.2",
    "claude-2",
    "claude-2.1",
    "claude-instant-v1-100k",
    "gpt-4-1106-preview",
    "gpt-4-0125-preview"
]

class ChatBody(BaseModel):
    model: Any
    messages: Any
    stream: Optional[bool] = False
    max_tokens: Optional[int] = 4000
    presence_penalty: Optional[float] = 1.0
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0

    @classmethod
    def model_check(cls, model):
        if not isinstance(model, str) or model not in (models + premium_models):
            raise ValueError('Invalid model.')

    @classmethod  
    def messages_check(cls, messages):
        if not isinstance(messages, list):
            raise ValueError('Invalid messages.')

    @field_validator("model")
    def validate_model(cls, v):
        cls.model_check(v)
        return v

    @field_validator("messages")
    def validate_messages(cls, v):
        cls.messages_check(v)
        return v

async def generate_completion_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=28))

async def generate_timestamp():
    return int(time.time())

async def streaming(text, completion_id, completion_timestamp, model):
    try:
        for chunk in text:
            content = create_completion_data(chunk, completion_id, completion_timestamp, model)
            yield f"data: {content}\n\n"
            await asyncio.sleep(0.001)
        yield "data: [DONE]"
    except GeneratorExit:
        pass

def create_completion_data(chunk, completion_id, completion_timestamp, model):
    return ujson.dumps({"id": f"chatcmpl-{completion_id}", "object": "chat.completion.chunk", "created": completion_timestamp, "model": model, "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}]}, separators=(",",":"))

@app.post("/unf/chat/completions/{rest}", dependencies=[Depends(user_checks)])
@app.post("/unf/chat/completions", dependencies=[Depends(user_checks)])
async def chat(request: Request, data: ChatBody) -> dict:
    messages, model, stream, key, origin = data.messages, data.model, data.stream, request.headers.get("Authorization", "").replace("Bearer ", ""), request.headers.get("HTTP-Referer", "") or request.headers.get("Referer", "") or request.headers.get("Origin", "")

    premium = await DatabaseManager.premium_check(key)

    if stream:
        raise HTTPException(detail={"error": {"message": "Streaming is not supported here.", "type": "error", "param": None, "code": 403}}, status_code=403)
    elif models in premium_models and not premium:
        raise HTTPException(detail={"error": {"message": f"You don't have access to '{model}'.", "type": "error", "param": None, "code": 400}}, status_code=400)

    content = await openai.openai(data.model_dump())

    if not content or content == "":
        raise HTTPException(detail={"error": {"message": f"The provider for {model} sent an invalid response.", "type": "error", "param": None, "code": 500}}, status_code=500)

    completion_id, completion_timestamp = await generate_completion_id(), await generate_timestamp()
    prompt_tokens, completion_tokens = await helpers.tokenize(''.join([str(message['content']) for message in messages])), await helpers.tokenize(content)

    helpers.create_background_task(DatabaseManager.credits_update(key, round((prompt_tokens + completion_tokens) / 10)))

    if stream:
        return StreamingResponse(content=streaming(content, completion_id, completion_timestamp, model), media_type="text/event-stream", status_code=200)
    else:
        return {
            "id": f"chatcmpl-{completion_id}",
            "object": "chat.completion",
            "created": completion_timestamp,
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens, "total_tokens": prompt_tokens + completion_tokens}
        }
