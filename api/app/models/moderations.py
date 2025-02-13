from pydantic import BaseModel, field_validator
from typing import List, Union

class ModerationRequest(BaseModel):
    model: str
    input: Union[str, List[str]]

    @field_validator('input')
    @classmethod
    def validate_input(cls, value: Union[str, List[str]]) -> Union[str, List[str]]:
        if isinstance(value, str):
            if not value:
                raise ValueError('The input field must not have an empty string')
        elif isinstance(value, list):
            if not value or any(not item for item in value):
                raise ValueError('The input field must not have an empty array')

        return value