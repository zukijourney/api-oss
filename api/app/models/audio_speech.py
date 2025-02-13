from pydantic import BaseModel, field_validator
from typing import Optional

class SpeechRequest(BaseModel):
    model: str
    input: str
    voice: Optional[str] = None

    @field_validator('input')
    @classmethod
    def validate_input(cls, value: str) -> str:
        if not value:
            raise ValueError('The input field must not have an empty string')
        return value