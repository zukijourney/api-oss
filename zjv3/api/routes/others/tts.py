from fastapi import APIRouter, Depends, Response, HTTPException
from ...providers.openai import openai
from ...utils.security import user_checks
from pydantic import BaseModel, field_validator
from typing import Any

app = APIRouter()

voices = [
    "alloy", "echo", "fable",
    "onyx", "nova", "shimmer"
]

class TtsBody(BaseModel):
    input: Any
    model: Any
    voice: Any

    @classmethod
    def check_input(cls, input):
        if not isinstance(input, str) or len(input) > 4096:
            raise ValueError('Invalid input.')
        
    @classmethod
    def check_model(cls, model):
        if not isinstance(model, str) or model != "tts-1":
            raise ValueError('Invalid model.')
        
    @classmethod
    def check_voice(cls, voice):
        if not isinstance(voice, str) or voice not in voices:
            raise ValueError('Invalid voice.')

    @field_validator("input")
    def validate_input(cls, v):
        cls.check_input(v)
        return v

    @field_validator("model")
    def validate_model(cls, v):
        cls.check_model(v)
        return v
    
    @field_validator("voice")
    def validate_voice(cls, v):
        cls.check_voice(v)
        return v

@app.post("/v1/audio/speech", dependencies=[Depends(user_checks)])
async def tts(data: TtsBody) -> None:
    content = await openai(data.input, data.voice)

    if content is None:
        raise HTTPException(detail={
            "error": {
                "message": "The provider sent an invalid response.",
                "type": "error",
                "param": None,
                "code": 500
            }
        }, status_code=500)

    return Response(content=content, media_type="audio/mpeg", headers={"Content-Disposition": "attachment;filename=audio.mp3"}, status_code=200)
