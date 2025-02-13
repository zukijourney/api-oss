from pydantic import BaseModel, field_validator
from typing import Optional

class TextTranslationsRequest(BaseModel):
    model: str
    text: str
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None

    @field_validator('text')
    @classmethod
    def validate_text(cls, value: str) -> str:
        if not value:
            raise ValueError('The text field must not have an empty string')
        return value