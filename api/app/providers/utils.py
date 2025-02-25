import time
import ujson
import random
import string
import functools
import httpx
from dataclasses import dataclass
from fastapi import Request
from typing import List, Dict, Any, Callable, Coroutine, Optional
from ..responses import StreamingResponseWithStatusCode
from ..providers import BaseProvider
from ..core import ProviderManager, settings

@dataclass
class WebhookConfig:
    success_color: int = 0x00FF00
    error_color: int = 0xFF0000
    admin_id: str = '325699845031723010'
    error_alert: str = '⚠️ **Error Alert**'

class ErrorHandler:
    def __init__(self):
        self.provider_manager = ProviderManager()
        self.excluded_providers = []

    @classmethod
    def retry_provider(cls, max_retries: int) -> Callable:
        def decorator(func: Callable[..., Coroutine]) -> Callable:
            @functools.wraps(func)
            async def wrapped(*args, **kwargs) -> Any:
                instance = cls()

                current_func = func

                for attempt in range(max_retries):
                    try:
                        response = await current_func(*args, **kwargs)
                    except TypeError:
                        continue

                    if isinstance(response, StreamingResponseWithStatusCode):
                        first_chunk, status_code = await response.body_iterator.__anext__()
                        if status_code == 200:
                            return await instance._wrap_streaming_response(
                                response, first_chunk, status_code
                            )
                    elif getattr(response, 'status_code', 0) == 200:
                        return response

                    if attempt == 2:
                        args = args[1:]

                    if attempt >= 2:
                        instance.excluded_providers.append(
                            current_func.__qualname__.split('.')[0]
                        )
                        current_func = await instance._get_alternative_provider(
                            current_func, args, kwargs
                        )
                        if not current_func:
                            current_func = func

                return response

            return wrapped
        return decorator

    def _requires_vision(self, messages: Optional[List[Dict[str, Any]]]) -> bool:
        if not messages:
            return False

        return any(
            isinstance(msg.get('content'), list) and
            any(item.get('type') == 'image_url' for item in msg['content'])
            for msg in messages
        )

    async def _get_alternative_provider(
        self,
        current_func: Callable,
        args: tuple,
        kwargs: dict
    ) -> Optional[Callable]:
        provider = await self.provider_manager.get_best_provider(
            model=kwargs.get('model'),
            vision=self._requires_vision(kwargs.get('messages')),
            tools=kwargs.get('tools', False),
            excluded_providers=self.excluded_providers
        )

        if not provider:
            return None

        provider_class = BaseProvider.get_provider_class(provider['name'])

        if not provider_class:
            return None

        return getattr(provider_class, current_func.__name__)

    async def _wrap_streaming_response(
        self,
        response: StreamingResponseWithStatusCode,
        first_chunk: str,
        status_code: int
    ) -> StreamingResponseWithStatusCode:
        async def iterator():
            yield first_chunk, status_code
            async for chunk, status in response.body_iterator:
                yield chunk, status
    
        return StreamingResponseWithStatusCode(
            content=iterator(),
            media_type='text/event-stream'
        )

class MessageFormatter:
    @staticmethod
    def format_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        return '\n'.join(
            content_part['text']
            for content_part in content
            if content_part['type'] == 'text'
        )

    @staticmethod
    def format_messages(messages: List[Dict[str, Any]]) -> str:
        return '\n'.join(
            f'{msg["role"]}: {MessageFormatter.format_content(msg["content"])}'
            for msg in messages
        )

class ResponseGenerator:
    @staticmethod
    def generate_error(message: str, provider_id: str) -> str:
        error_response = {
            'error': {
                'message': message,
                'provider_id': provider_id,
                'type': 'invalid_response_error',
                'code': 500
            }
        }
        return ResponseGenerator._serialize_json(error_response)

    @staticmethod
    def generate_chunk(
        content: str,
        model: str,
        system_fp: str,
        completion_id: str,
        provider_id: str
    ) -> str:
        chunk_response = {
            'provider_id': provider_id,
            'id': completion_id,
            'object': 'chat.completion.chunk',
            'created': int(time.time()),
            'model': model,
            'choices': [
                {
                    'index': 0,
                    'delta': {
                        'role': 'assistant',
                        'content': content
                    }
                }
            ],
            'system_fingerprint': system_fp
        }
        return ResponseGenerator._serialize_json(chunk_response, False)

    @staticmethod
    def _serialize_json(obj: Dict[str, Any], indented: bool = True) -> str:
        if indented:
            return ujson.dumps(
                obj=obj,
                ensure_ascii=False,
                allow_nan=False,
                indent=4,
                separators=(', ', ': '),
                escape_forward_slashes=False
            )

        return ujson.dumps(
            obj=obj,
            ensure_ascii=False,
            allow_nan=False,
            escape_forward_slashes=False
        )

class IDGenerator:
    COMPLETION_PREFIX = 'chatcmpl-A'
    FINGERPRINT_PREFIX = 'fp_'
    
    @staticmethod
    def _generate_random_string(length: int, chars: str) -> str:
        return ''.join(random.choices(chars, k=length))

    @classmethod
    def generate_completion_id(cls) -> str:
        return f'{cls.COMPLETION_PREFIX}{cls._generate_random_string(29, string.ascii_letters + string.digits)}'

    @classmethod
    def generate_fingerprint(cls) -> str:
        return f'{cls.FINGERPRINT_PREFIX}{cls._generate_random_string(10, string.hexdigits.lower())}'

class WebhookManager:
    def __init__(self):
        self.config = WebhookConfig()
        self.blacklisted_providers = ['goo', 'su', 'gog', 'got', 'ch', 'hy']

    def _create_embed_data(
        self,
        is_error: bool,
        model: str,
        pid: str,
        user_id: str,
        exception: Optional[str] = None
    ) -> Dict[str, Any]:
        if exception and len(exception) > 1000:
            exception = exception[1000:]

        return {
            'title': 'Status Update',
            'color': self.config.error_color if is_error else self.config.success_color,
            'fields': [
                {
                    'name': 'Status',
                    'value': 'Failed' if is_error else 'Success',
                    'inline': True
                },
                {
                    'name': 'Model',
                    'value': model if model else 'Unknown',
                    'inline': True
                },
                {
                    'name': 'Error',
                    'value': exception if exception else 'No Error.',
                    'inline': True
                },
                {
                    'name': 'PID',
                    'value': pid if pid else 'No PID.',
                    'inline': True
                },
                {
                    'name': 'User',
                    'value': f'<@{user_id}>',
                    'inline': True
                }
            ],
            'footer': {
                'text': f'Timestamp: {time.strftime("%Y-%m-%d %H:%M:%S")}'
            }
        }

    def _create_payload(
        self,
        is_error: bool,
        embed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        payload = {'embeds': [embed_data]}
        
        if is_error:
            payload['content'] = f'{self.config.error_alert} <@{self.config.admin_id}>: WAKE THE FUCK UP'
        
        return payload

    @classmethod
    async def send_to_webhook(
        cls,
        request: Request,
        is_error: bool,
        model: str,
        pid: str,
        exception: Optional[str] = None
    ) -> None:
        instance = cls()

        if pid in instance.blacklisted_providers:
            return

        embed_data = instance._create_embed_data(
            is_error=is_error,
            model=model,
            pid=pid,
            user_id=request.state.user['user_id'],
            exception=exception
        )
        
        payload = instance._create_payload(is_error, embed_data)

        async with httpx.AsyncClient() as client:
            await client.post(settings.webhook_url, json=payload)


from curl_cffi.requests import AsyncSession, Response
from curl_cffi import CurlMime
has_curl_mime = True
from curl_cffi.requests import CurlWsFlag
has_curl_ws = True
from typing import AsyncGenerator, Any
from functools import partialmethod
import json

class StreamResponse:
    """
    A wrapper class for handling asynchronous streaming responses.

    Attributes:
        inner (Response): The original Response object.
    """

    def __init__(self, inner: Response) -> None:
        """Initialize the StreamResponse with the provided Response object."""
        self.inner: Response = inner

    async def text(self) -> str:
        """Asynchronously get the response text."""
        return await self.inner.atext()

    def raise_for_status(self) -> None:
        """Raise an HTTPError if one occurred."""
        self.inner.raise_for_status()

    async def json(self, **kwargs) -> Any:
        """Asynchronously parse the JSON response content."""
        return json.loads(await self.inner.acontent(), **kwargs)

    def iter_lines(self) -> AsyncGenerator[bytes, None]:
        """Asynchronously iterate over the lines of the response."""
        return  self.inner.aiter_lines()

    def iter_content(self) -> AsyncGenerator[bytes, None]:
        """Asynchronously iterate over the response content."""
        return self.inner.aiter_content()

    async def __aenter__(self):
        """Asynchronously enter the runtime context for the response object."""
        inner: Response = await self.inner
        self.inner = inner
        self.request = inner.request
        self.status: int = inner.status_code
        self.reason: str = inner.reason
        self.ok: bool = inner.ok
        self.headers = inner.headers
        self.cookies = inner.cookies
        return self

    async def __aexit__(self, *args):
        """Asynchronously exit the runtime context for the response object."""
        await self.inner.aclose()

class StreamSession(AsyncSession):
    """
    An asynchronous session class for handling HTTP requests with streaming.

    Inherits from AsyncSession.
    """

    def request(
        self, method: str, url: str, **kwargs
    ) -> StreamResponse:
        if isinstance(kwargs.get("data"), CurlMime):
            kwargs["multipart"] = kwargs.pop("data")
        """Create and return a StreamResponse object for the given HTTP request."""
        return StreamResponse(super().request(method, url, stream=True, **kwargs))

    def ws_connect(self, url, *args, **kwargs):
        return WebSocket(self, url, **kwargs)

    def _ws_connect(self, url, **kwargs):
        return super().ws_connect(url, **kwargs)

    # Defining HTTP methods as partial methods of the request method.
    head = partialmethod(request, "HEAD")
    get = partialmethod(request, "GET")
    post = partialmethod(request, "POST")
    put = partialmethod(request, "PUT")
    patch = partialmethod(request, "PATCH")
    delete = partialmethod(request, "DELETE")
    options = partialmethod(request, "OPTIONS")

if has_curl_mime:
    class FormData(CurlMime):
        def add_field(self, name, data=None, content_type: str = None, filename: str = None) -> None:
            self.addpart(name, content_type=content_type, filename=filename, data=data)
else:
    class FormData():
        def __init__(self) -> None:
            raise RuntimeError("CurlMimi in curl_cffi is missing | pip install -U g4f[curl_cffi]")

class WebSocket():
    def __init__(self, session, url, **kwargs) -> None:
        if not has_curl_ws:
            raise RuntimeError("CurlWsFlag in curl_cffi is missing | pip install -U g4f[curl_cffi]")
        self.session: StreamSession = session
        self.url: str = url
        del kwargs["autoping"]
        self.options: dict = kwargs

    async def __aenter__(self):
        self.inner = await self.session._ws_connect(self.url, **self.options)
        return self

    async def __aexit__(self, *args):
        await self.inner.aclose()

    async def receive_str(self, **kwargs) -> str:
        bytes, _ = await self.inner.arecv()
        return bytes.decode(errors="ignore")

    async def send_str(self, data: str):
        await self.inner.asend(data.encode(), CurlWsFlag.TEXT)