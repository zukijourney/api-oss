from pydantic import BaseModel, field_validator
from typing import List, Iterable, Optional, Any, Union

class EmbeddingsRequest(BaseModel):
    model: str
    input: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]]
    dimensions: Optional[int] = None

    @field_validator('input')
    @classmethod
    def validate_input(
        cls,
        value: Any
    ) -> Any:
        if isinstance(value, str) or isinstance(value, list):
            if not value:
                raise ValueError(
                    'The input field must not have an empty string/array'
                )
        elif isinstance(value, Iterable) and not isinstance(value, str):
            if all(isinstance(item, Iterable) for item in value) and not isinstance(value[0], str):
                if not all(sublist for sublist in value):
                    raise ValueError(
                        'The input field must not have an empty sub-array'
                    )
            else:
                if not value:
                    raise ValueError(
                        'The input field must not have an empty iterable'
                    )

        return value