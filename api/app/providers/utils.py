import time
import functools
import httpx
from dataclasses import dataclass
from collections import deque
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
                    response = await current_func(*args, **kwargs)

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

class WebhookManager:
    def __init__(self):
        self.config = WebhookConfig()
        self.recent_exceptions = deque(maxlen=50)
        self.blacklisted_providers = []

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

    def _should_send_exception(self, exception: Optional[str]) -> bool:
        if not exception:
            return True

        exception_key = exception[:100]

        current_time = time.time()

        for exc_key, timestamp in self.recent_exceptions:
            if exc_key == exception_key and current_time - timestamp < 120:
                return False

        self.recent_exceptions.append((exception_key, current_time))
        return True

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

        if is_error and not instance._should_send_exception(exception):
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