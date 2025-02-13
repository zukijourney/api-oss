import tiktoken
import importlib
import inspect
from fastapi import FastAPI, APIRouter, Request
from pathlib import Path
from typing import Union, List, Optional
from dataclasses import dataclass
from .models import ChatRequest, Message, TextContentPart, ImageContentPart

@dataclass
class TokenizerConfig:
    encoding_name: str = 'o200k_base'
    non_text_token_count: int = 100

class TokenCounter:
    def __init__(self, config: Optional[TokenizerConfig] = None):
        self.config = config or TokenizerConfig()
        self.encoding = tiktoken.get_encoding(self.config.encoding_name)

    def count_message_content_tokens(
        self,
        content: Union[str, List[Union[TextContentPart, ImageContentPart]]]
    ) -> int:
        if isinstance(content, str):
            return len(self.encoding.encode(content))

        return sum(
            len(self.encoding.encode(part.text))
            if part.type == 'text'
            else self.config.non_text_token_count
            for part in content
        )

    def count_message_tokens(self, message: Optional[Union[Message, str]]) -> int:
        if not message:
            return 0

        if isinstance(message, str):
            return len(self.encoding.encode(message))

        return self.count_message_content_tokens(message.content)

    def count_request_tokens(self, data: ChatRequest) -> int:
        return sum(
            self.count_message_tokens(msg)
            for msg in data.messages
        )

class APIKeyExtractor:
    def __init__(self, config: Optional[TokenizerConfig] = None):
        self.config = config or TokenizerConfig()

    def extract_api_key(self, request: Request) -> str:
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return 'none'

        return auth_header.replace('Bearer ', '', 1)

    def validate_api_key(self, api_key: str) -> bool:
        return (
            api_key != 'none' and
            len(api_key.strip()) > 0
        )

class RequestProcessor:
    def __init__(
        self,
        token_counter: Optional[TokenCounter] = None,
        key_extractor: Optional[APIKeyExtractor] = None,
        config: Optional[TokenizerConfig] = None
    ):
        self.config = config or TokenizerConfig()
        self.token_counter = token_counter or TokenCounter(self.config)
        self.key_extractor = key_extractor or APIKeyExtractor(self.config)

    def count_tokens(self, data: Union[ChatRequest, str]) -> int:
        if isinstance(data, ChatRequest):
            return self.token_counter.count_request_tokens(data)
        return self.token_counter.count_message_tokens(data)

    def get_api_key(self, request: Request) -> str:
        return self.key_extractor.extract_api_key(request)

class RouteLoader:
    @staticmethod
    def load(app: FastAPI, base_dir: str):
        base_path = Path(base_dir)

        if (base_path / 'route.py').exists():
            module_path = str(base_path / 'route.py').replace('/', '.').replace('\\', '.')[:-3]
            module = importlib.import_module(module_path)

            for _, obj in inspect.getmembers(module):
                if isinstance(obj, APIRouter):
                    print('Adding route: /')
                    app.include_router(obj)

        def _process_directory(
            current_path: Path,
            current_path_name: Optional[str] = None
        ) -> None:
            if current_path_name:
                current_path = base_path / current_path_name

            try:
                relative_path = current_path.relative_to(base_path)

                for item in current_path.iterdir():
                    if item.name.startswith('__') or not (item.is_dir() or item.suffix == '.py'):
                        continue

                    if item.is_file() and item.stem != 'route':
                        route_name = str(item)[:-3].replace(str(base_path), '').replace('[', '{').replace(']', '}')
                        module_path = str(item).replace('/', '.').replace('\\', '.')[:-3]

                        module = importlib.import_module(module_path)
                        
                        for _, obj in inspect.getmembers(module):
                            if isinstance(obj, APIRouter):
                                print(f'Adding route: {route_name}')
                                app.include_router(obj, prefix=route_name)

                    elif item.is_dir():
                        route_name = item.name.replace('[', '{').replace(']', '}')

                        if (item / 'route.py').exists():
                            module_path = str(item / 'route.py').replace('/', '.').replace('\\', '.')[:-3]
                            module = importlib.import_module(module_path)
                            
                            for _, obj in inspect.getmembers(module):
                                if isinstance(obj, APIRouter):
                                    print(f'Adding route: /{route_name}')
                                    app.include_router(obj, prefix=route_name)
                        
                        _process_directory(item, str(relative_path / item.name))

            except Exception as e:
                print(f'Error processing {current_path}: {e}')

        _process_directory(base_path)