from fastapi import APIRouter, Depends
from ...providers.openai import openai
from ...utils.security import user_checks
from pydantic import BaseModel, field_validator
from typing import Any

app = APIRouter()

models = [
     "text-embedding-ada-002",
     "text-embedding-3-small",
     "text-embedding-3-large",
     "e5-mistral-7b-instruct"
]

class EmbeddingsBody(BaseModel):
    input: Any
    model: Any

    @classmethod
    def check_input(cls, input):
        if not isinstance(input, str):
            raise ValueError('Invalid input.')
        
    @classmethod
    def check_model(cls, model):
        if not isinstance(model, str) or model not in models:
            raise ValueError('Invalid model.')

    @field_validator("input")
    def validate_input(cls, v):
        cls.check_input(v)
        return v
    
    @field_validator("model")
    def validate_model(cls, v):
        cls.check_model(v)
        return v

@app.post("/v1/embeddings", dependencies=[Depends(user_checks)])
async def embeddings(data: EmbeddingsBody) -> None:
    response = await openai(data.input, data.model)

    return {
        "data": [
            {
                "embedding": response,
                "index": 0,
                "object": "embedding",
            }
        ],
        "model": data.model,
        "object": "list",
        "usage": {
            "prompt_tokens": 0, 
            "total_tokens": 0
        }
    }
