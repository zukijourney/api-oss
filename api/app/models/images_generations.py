from pydantic import BaseModel, field_validator
from typing import Literal, Optional

class ImageRequest(BaseModel):
    model: str
    prompt: str
    n: int = 1
    size: Literal['256x256', '512x512', '1024x1024', '1792x1024', '1024x1792'] = '1024x1024'
    negative_prompt: Optional[str] = None

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, value: str) -> str:
        if not value:
            raise ValueError('The prompt field must not have an empty string')
        return value