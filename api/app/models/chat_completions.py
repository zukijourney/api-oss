from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional, Union, Literal

class ImageURL(BaseModel):
    detail: Literal['auto', 'low', 'high'] = 'auto'
    url: str

class ImageContentPart(BaseModel):
    type: Literal['image_url']
    image_url: ImageURL

class TextContentPart(BaseModel):
    type: Literal['text']
    text: str

class Message(BaseModel):
    role: Literal['user', 'assistant', 'system', 'developer']
    content: Union[str, List[Union[ImageContentPart, TextContentPart]]]

class ChatRequest(BaseModel):
    model: str
    messages: List[Message] = Field(min_length=1)
    stream: bool = False
    temperature: Optional[float] = Field(default=None, le=2.0, ge=0.0)
    top_p: Optional[float] = Field(default=None, le=1.0, ge=0.0)
    presence_penalty: Optional[float] = Field(default=None, le=1.0, ge=0.0)
    frequency_penalty: Optional[float] = Field(default=None, le=1.0, ge=0.0)
    max_tokens: Optional[int] = None
    max_completion_tokens: Optional[int] = None
    tool_choice: Optional[Literal['none', 'auto', 'required']] = None
    tools: Optional[List[Dict[str, Any]]] = None
    provider_name: Optional[str] = None

    @field_validator('messages')
    @classmethod
    def validate_messages(cls, messages: List[Message]) -> List[Message]:
        if not any(msg.role == 'user' for msg in messages):
            raise ValueError('Messages must contain at least one user message')

        if messages[0].role == 'assistant':
            raise ValueError('First message must be from user or system')

        for msg in messages:
            if isinstance(msg.content, str):
                if not msg.content:
                    raise ValueError('Message content cannot be empty')
                continue

            if msg.role != 'user' and any(isinstance(part, ImageContentPart) for part in msg.content):
                raise ValueError('Array image content only allowed for user messages')

            if not msg.content:
                raise ValueError('Message content array cannot be empty')

            if any(isinstance(part, ImageContentPart) for part in msg.content) and \
                not any(isinstance(part, TextContentPart) for part in msg.content):
                raise ValueError('An array with image content must also contain text content')

            for part in msg.content:
                if isinstance(part, ImageContentPart) and not part.image_url.url:
                    raise ValueError('Image URL cannot be empty')
                if isinstance(part, TextContentPart) and not part.text:
                    raise ValueError('Text content cannot be empty')

        return messages