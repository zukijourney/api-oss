import ujson
import time
import httpx
import traceback
import re
from dataclasses import dataclass
from fastapi import Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any, Tuple, Iterable, AsyncGenerator, Optional, Union
from ...responses import PrettyJSONResponse
from ...core import UserManager, ProviderManager, settings
from ...utils import RequestProcessor
from ..ai_models import Model
from ..base_provider import BaseProvider, ProviderConfig
from ..utils import WebhookManager, ErrorHandler

@dataclass(frozen=True)
class OpenAIConfig:
    base_url: str = 'https://api.openai.com'
    provider_id: str = 'oai'
    timeout: int = 100
    long_timeout: int = 10000

class SubProviderManager:
    def __init__(self, db_client: AsyncIOMotorClient, provider_name: str):
        self.collection = db_client['db']['sub_providers']
        self.provider_name = provider_name

    async def get_available_provider(self, model: str) -> Optional[Dict[str, Any]]:
        sub_providers = await self.collection.find({
            'main_provider': self.provider_name,
            'models.api_name': {'$in': [model]},
            '$or': [
                {'working': True},
                {'working': {'$exists': False}}
            ]
        }).to_list(length=None)

        if not sub_providers:
            return None

        return min(
            sub_providers,
            key=lambda x: (x.get('usage', 0), x.get('last_used', 0))
        )

    async def update_provider(
        self,
        api_key: str,
        new_data: Dict[str, Any]
    ) -> None:
        update_data = {k: v for k, v in new_data.items() if k != '_id'}
        await self.collection.update_many(
            filter={'api_key': api_key},
            update={'$set': update_data}
        )

    async def disable_provider(
        self,
        api_key: str
    ) -> None:
        await self.collection.update_many(
            filter={'api_key': api_key},
            update={'$set': {'working': False}}
        )

class APIClient:
    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=self.config.timeout
        )

    async def make_request(
        self,
        endpoint: str,
        method: str,
        sub_provider: Dict[str, Any],
        data: Dict[str, Any],
        stream: bool = False,
        files: Dict[str, Any] = None,
        long_timeout: bool = False
    ) -> httpx.Response:
        headers = {
            'authorization': f'Bearer {sub_provider["api_key"]}',
            'openai-organization': sub_provider.get('organization', '')
        }
        url = f'{self.config.base_url}/v1/{endpoint}'

        if long_timeout:
            self.client.timeout = self.config.long_timeout

        return await self.client.send(
            self.client.build_request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                files=files
            ),
            stream=stream
        )

class ResponseHandler:
    def __init__(self, config: OpenAIConfig):
        self.config = config

    def create_error_response(
        self,
        message: str = 'Something went wrong. Try again later.',
        status_code: int = 500,
        error_type: str = 'invalid_response_error'
    ) -> PrettyJSONResponse:
        return PrettyJSONResponse(
            content={
                'error': {
                    'message': re.sub(r'[^/]+\.py', '', message),
                    'provider_id': self.config.provider_id,
                    'type': error_type,
                    'code': status_code
                }
            },
            status_code=status_code
        )

    def create_completion_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'provider_id': self.config.provider_id,
            **response_data
        }

    def create_audio_response(self, content: bytes) -> Response:
        return Response(
            content=content,
            media_type='audio/mpeg',
            headers={'content-disposition': 'attachment;filename=audio.mp3'}
        )

class MetricsManager:
    def __init__(
        self,
        user_manager: UserManager,
        provider_manager: ProviderManager,
        sub_provider_manager: SubProviderManager
    ):
        self.user_manager = user_manager
        self.provider_manager = provider_manager
        self.sub_provider_manager = sub_provider_manager
        self.request_processor = RequestProcessor()

    async def update_user_credits(
        self,
        request: Request,
        model: str,
        token_count: int
    ) -> None:
        model_instance = Model.get_model(model)
        request.state.user['credits'] -= token_count * model_instance.pricing.multiplier
        await self.user_manager.update_user(request.state.user['user_id'], request.state.user)

    async def update_metrics(
        self,
        request: Request,
        model: str,
        sub_provider: Dict[str, Any],
        response_data: Dict[str, Any],
        start_time: float
    ) -> None:
        elapsed = time.time() - start_time
        word_count, token_count = self._calculate_counts(response_data)
        
        await self._update_provider_metrics(request, model, elapsed, word_count)
        await self._update_sub_provider_metrics(sub_provider)
        await self.update_user_credits(
            request, model, token_count
        )

    def _calculate_counts(self, response_data: Dict[str, Any]) -> Tuple[int, int]:
        word_count = sum(
            len(choice['message']['content'])
            for choice in response_data['choices']
            if choice.get('message', {}).get('content', '')
        ) + self._count_additional_fields(response_data)

        token_count = sum(
            self.request_processor.count_tokens(choice['message']['content'])
            for choice in response_data['choices']
            if choice.get('message', {}).get('content', '')
        )

        return word_count, token_count

    def _count_additional_fields(self, data: Dict[str, Any]) -> int:
        if isinstance(data, dict):
            return sum(
                self._count_additional_fields(v)
                for k, v in data.items()
                if k != 'message'
            )
        elif isinstance(data, list):
            return sum(self._count_additional_fields(item) for item in data)
        elif isinstance(data, str):
            return len(data.split())
        return 0

    async def update_streaming_metrics(
        self,
        request: Request,
        model: str,
        sub_provider: Dict[str, Any],
        start_time: float
    ) -> None:
        elapsed = time.time() - start_time
        await self._update_provider_metrics(request, model, elapsed, 1)
        await self._update_sub_provider_metrics(sub_provider)

    async def _update_provider_metrics(
        self,
        request: Request,
        model: str,
        elapsed: float,
        word_count: int
    ) -> None:
        latency = (elapsed / word_count) if word_count > 0 else 0

        request.state.provider['usage'][model] = request.state.provider['usage'].get(model, 0) + 1
        request.state.provider['latency'][model] = (
            (request.state.provider['latency'].get(model, 0) + latency) / 2 
            if request.state.provider['latency'].get(model, 0) != 0 
            else latency
        )

        await self.provider_manager.update_provider(
            request.state.provider_name,
            request.state.provider,
            model
        )

    async def _update_sub_provider_metrics(
        self,
        sub_provider: Dict[str, Any]
    ) -> None:
        sub_provider['usage'] = sub_provider.get('usage', 0) + 1
        sub_provider['last_used'] = time.time()
        await self.sub_provider_manager.update_provider(
            sub_provider['api_key'],
            sub_provider
        )

class StreamHandler:
    def __init__(
        self,
        metrics_manager: MetricsManager,
        config: OpenAIConfig
    ):
        self.metrics_manager = metrics_manager
        self.config = config
        self.request_processor = RequestProcessor()

    async def handle_stream(
        self,
        response: httpx.Response,
        request: Request,
        model: str,
        sub_provider: Dict[str, Any],
        start_time: float
    ) -> StreamingResponse:
        async def stream_generator() -> AsyncGenerator[str, None]:
            await self.metrics_manager.update_streaming_metrics(
                request, model, sub_provider, start_time
            )

            async for line in response.aiter_lines():
                if line.startswith('data: ') and not line.startswith('data: [DONE]'):
                    yield await self._process_chunk(request, model, line)

            yield 'data: [DONE]\n\n'

        return StreamingResponse(
            content=stream_generator(),
            media_type='text/event-stream',
            background=BackgroundTask(response.aclose)
        )

    async def _process_chunk(
        self,
        request: Request,
        model: str,
        line: str
    ) -> str:
        parsed_chunk = {
            'provider_id': self.config.provider_id,
            **ujson.loads(line[6:].strip())
        }
        token_count = sum(
            self.request_processor.count_tokens(choice.get('delta', {}).get('content', ''))
            for choice in parsed_chunk.get('choices', [{}])
        )

        await self.metrics_manager.update_user_credits(request, model, token_count)

        return f'data: {ujson.dumps(parsed_chunk)}\n\n'

class EndpointHandler:
    def __init__(
        self,
        api_client: APIClient,
        response_handler: ResponseHandler,
        metrics_manager: MetricsManager,
        stream_handler: StreamHandler,
        sub_provider_manager: SubProviderManager,
        provider_manager: ProviderManager,
        api_config: OpenAIConfig,
        provider_config: ProviderConfig
    ):
        self.api_client = api_client
        self.response_handler = response_handler
        self.metrics_manager = metrics_manager
        self.stream_handler = stream_handler
        self.sub_provider_manager = sub_provider_manager
        self.provider_manager = provider_manager
        self.api_config = api_config
        self.provider_config = provider_config
    
    async def _handle_error(
        self,
        request: Request,
        model: str,
        text: str
    ) -> None:
        await WebhookManager.send_to_webhook(
            request=request,
            is_error=True,
            model=model,
            pid=self.api_config.provider_id,
            exception=f'Error: {text}'
        )
        
        current_failure_count = request.state.provider['failures'].get(model, 0)
        request.state.provider['failures'][model] = current_failure_count + 1
        
        await self.provider_manager.update_provider(
            self.provider_config.name,
            request.state.provider
        )
    
    async def _handle_api_error(
        self,
        response: httpx.Response,
        stream: bool,
        sub_provider: Dict[str, Any],
        request: Request,
        model: str
    ) -> PrettyJSONResponse:
        if response.status_code in [401, 403, 404, 429]:
            await self.sub_provider_manager.disable_provider(
                sub_provider['api_key']
            )

        await self._handle_error(
            request,
            model,
            (await response.aread()).decode() if stream else response.text
        )
        return self.response_handler.create_error_response()

    async def handle_chat_completion(
        self,
        request: Request,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool,
        sub_provider: Dict[str, Any],
        start_time: float,
        **kwargs
    ) -> Union[PrettyJSONResponse, StreamingResponse]:
        if 'gpt-' not in model:
            kwargs.pop('max_tokens', None)
            kwargs.pop('temperature', None)

        if model == 'chatgpt-4o-latest':
            kwargs.pop('tool_choice', None)
            kwargs.pop('tools', None)

        response = await self.api_client.make_request(
            endpoint='chat/completions',
            method='POST',
            sub_provider=sub_provider,
            data={
                'model': model,
                'messages': messages,
                'stream': stream,
                **kwargs
            },
            stream=stream
        )

        if response.status_code != 200:
            return await self._handle_api_error(
                response, stream, sub_provider, request, model
            )

        if stream:
            return await self.stream_handler.handle_stream(
                response, request, model, sub_provider, start_time
            )
        
        json_response = response.json()

        await self.metrics_manager.update_metrics(
            request, model, sub_provider, json_response, start_time
        )
        return PrettyJSONResponse(
            self.response_handler.create_completion_response(json_response)
        )

    async def handle_images_generations(
        self,
        request: Request,
        model: str,
        prompt: str,
        sub_provider: Dict[str, Any]
    ) -> PrettyJSONResponse:
        response = await self.api_client.make_request(
            endpoint='images/generations',
            method='POST',
            sub_provider=sub_provider,
            data={'model': model, 'prompt': prompt},
            long_timeout=True
        )

        if response.status_code != 200:
            return await self._handle_api_error(
                response, False, sub_provider, request, model
            )

        model_instance = Model.get_model(model)
        request.state.user['credits'] -= model_instance.pricing.price

        await self.metrics_manager.user_manager.update_user(
            request.state.user['user_id'],
            request.state.user
        )

        return PrettyJSONResponse(
            self.response_handler.create_completion_response(response.json())
        )

    async def handle_embeddings(
        self,
        request: Request,
        model: str,
        input_data: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        sub_provider: Dict[str, Any],
        **kwargs
    ) -> PrettyJSONResponse:
        response = await self.api_client.make_request(
            endpoint='embeddings',
            method='POST',
            sub_provider=sub_provider,
            data={'model': model, 'input': input_data, **kwargs},
            long_timeout=True
        )

        if response.status_code != 200:
            return await self._handle_api_error(
                response, False, sub_provider, request, model
            )

        model_instance = Model.get_model(model)
        request.state.user['credits'] -= model_instance.pricing.price

        await self.metrics_manager.user_manager.update_user(
            request.state.user['user_id'],
            request.state.user
        )

        return PrettyJSONResponse(
            self.response_handler.create_completion_response(response.json())
        )

    async def handle_moderations(
        self,
        request: Request,
        model: str,
        input_data: Union[str, List[str]],
        sub_provider: Dict[str, Any]
    ) -> PrettyJSONResponse:
        response = await self.api_client.make_request(
            endpoint='moderations',
            method='POST',
            sub_provider=sub_provider,
            data={'model': model, 'input': input_data},
            long_timeout=True
        )

        if response.status_code != 200:
            return await self._handle_api_error(
                response, False, sub_provider, request, model
            )

        model_instance = Model.get_model(model)
        request.state.user['credits'] -= model_instance.pricing.price

        await self.metrics_manager.user_manager.update_user(
            request.state.user['user_id'],
            request.state.user
        )

        return PrettyJSONResponse(
            self.response_handler.create_completion_response(response.json())
        )

    async def handle_audio_speech(
        self,
        request: Request,
        model: str,
        input_text: str,
        sub_provider: Dict[str, Any],
        **kwargs
    ) -> Response:
        response = await self.api_client.make_request(
            endpoint='audio/speech',
            method='POST',
            sub_provider=sub_provider,
            data={'model': model, 'input': input_text, **kwargs},
            long_timeout=True
        )

        if response.status_code != 200:
            return await self._handle_api_error(
                response, False, sub_provider, request, model
            )

        model_instance = Model.get_model(model)
        request.state.user['credits'] -= model_instance.pricing.price + len(input_text)
        await self.metrics_manager.user_manager.update_user(
            request.state.user['user_id'],
            request.state.user
        )

        return self.response_handler.create_audio_response(response.content)

    async def handle_audio_transcriptions(
        self,
        request: Request,
        model: str,
        file: UploadFile,
        sub_provider: Dict[str, Any]
    ) -> PrettyJSONResponse:
        response = await self.api_client.make_request(
            endpoint='audio/transcriptions',
            method='POST',
            sub_provider=sub_provider,
            data={},
            files={'model': (None, model), 'file': (file.filename, file.file)},
            long_timeout=True
        )

        if response.status_code != 200:
            return await self._handle_api_error(
                response, False, sub_provider, request, model
            )

        model_instance = Model.get_model(model)
        request.state.user['credits'] -= model_instance.pricing.price

        await self.metrics_manager.user_manager.update_user(
            request.state.user['user_id'],
            request.state.user
        )

        return PrettyJSONResponse(
            self.response_handler.create_completion_response(response.json())
        )

    async def handle_audio_translations(
        self,
        request: Request,
        model: str,
        file: UploadFile,
        sub_provider: Dict[str, Any]
    ) -> PrettyJSONResponse:
        response = await self.api_client.make_request(
            endpoint='audio/translations',
            method='POST',
            sub_provider=sub_provider,
            data={},
            files={'model': (None, model), 'file': (file.filename, file.file)},
            long_timeout=True
        )

        if response.status_code != 200:
            return await self._handle_api_error(
                response, False, sub_provider, request, model
            )

        model_instance = Model.get_model(model)
        request.state.user['credits'] -= model_instance.pricing.price

        await self.metrics_manager.user_manager.update_user(
            request.state.user['user_id'],
            request.state.user
        )

        return PrettyJSONResponse(
            self.response_handler.create_completion_response(response.json())
        )

class OpenAI(BaseProvider):
    config = ProviderConfig(
        name='OpenAI',
        supports_vision=True,
        supports_tool_calling=True,
        supports_real_streaming=True,
        free_models=[
            'gpt-3.5-turbo',
            'gpt-4o',
            'gpt-4o-mini',
            'tts-1',
            'text-embedding-3-small',
            'text-embedding-3-large',
            'omni-moderation-latest',
            'whisper-1'
        ],
        paid_models=[
            'gpt-4',
            'gpt-4-1106-preview',
            'gpt-4-0125-preview',
            'gpt-4-turbo',
            'chatgpt-4o-latest',
            'gpt-4o-2024-11-20',
            'o1-mini',
            'o1-preview',
            'dall-e-3',
            'tts-1-hd'
        ],
        early_access_models=[
            'o1',
            'o3-mini'
        ]
    )

    def __init__(self):
        super().__init__()
        self.api_config = OpenAIConfig()
        self.user_manager = UserManager()
        self.provider_manager = ProviderManager()
        self.sub_provider_manager = SubProviderManager(
            AsyncIOMotorClient(settings.db_url),
            self.config.name
        )
        self.api_client = APIClient(self.api_config)
        self.response_handler = ResponseHandler(self.api_config)
        self.metrics_manager = MetricsManager(
            self.user_manager,
            self.provider_manager,
            self.sub_provider_manager
        )
        self.stream_handler = StreamHandler(
            self.metrics_manager,
            self.api_config
        )
        self.endpoint_handler = EndpointHandler(
            self.api_client,
            self.response_handler,
            self.metrics_manager,
            self.stream_handler,
            self.sub_provider_manager,
            self.provider_manager,
            self.api_config,
            self.config
        )

    @classmethod
    @ErrorHandler.retry_provider(max_retries=10)
    async def chat_completions(
        cls,
        request: Request,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool,
        **kwargs
    ) -> Union[PrettyJSONResponse, StreamingResponse]:
        instance = cls()
        start_time = time.time()

        try:
            sub_provider = await instance.sub_provider_manager.get_available_provider(model)
            if not sub_provider:
                return instance.response_handler.create_error_response(
                    message='No sub-providers were found for the specified model. Try again later.',
                    status_code=503,
                    error_type='sub_provider_error'
                )

            await instance.metrics_manager.update_user_credits(
                request,
                model,
                request.state.token_count
            )

            return await instance.endpoint_handler.handle_chat_completion(
                request, model, messages, stream, sub_provider, start_time, **kwargs
            )

        except Exception:
            await instance.endpoint_handler._handle_error(
                request, model, traceback.format_exc()
            )
            return instance.response_handler.create_error_response(
                traceback.format_exc()
            )

    @classmethod
    async def images_generations(
        cls,
        request: Request,
        model: str,
        prompt: str,
        **_
    ) -> PrettyJSONResponse:
        instance = cls()

        try:
            sub_provider = await instance.sub_provider_manager.get_available_provider(model)
            if not sub_provider:
                return instance.response_handler.create_error_response(
                    message='No sub-providers were found for the specified model. Try again later.',
                    status_code=503,
                    error_type='sub_provider_error'
                )

            return await instance.endpoint_handler.handle_images_generations(
                request, model, prompt, sub_provider
            )

        except Exception:
            await instance.endpoint_handler._handle_error(
                request, model, traceback.format_exc()
            )
            return instance.response_handler.create_error_response(
                traceback.format_exc()
            )

    @classmethod
    async def embeddings(
        cls,
        request: Request,
        model: str,
        input: Union[str, List[str], Iterable[int], Iterable[Iterable[int]]],
        **kwargs
    ) -> PrettyJSONResponse:
        instance = cls()

        try:
            sub_provider = await instance.sub_provider_manager.get_available_provider(model)
            if not sub_provider:
                return instance.response_handler.create_error_response(
                    message='No sub-providers were found for the specified model. Try again later.',
                    status_code=503,
                    error_type='sub_provider_error'
                )

            return await instance.endpoint_handler.handle_embeddings(
                request, model, input, sub_provider, **kwargs
            )

        except Exception:
            await instance.endpoint_handler._handle_error(
                request, model, traceback.format_exc()
            )
            return instance.response_handler.create_error_response(
                traceback.format_exc()
            )

    @classmethod
    async def moderations(
        cls,
        request: Request,
        model: str,
        input: Union[str, List[str]]
    ) -> PrettyJSONResponse:
        instance = cls()

        try:
            sub_provider = await instance.sub_provider_manager.get_available_provider(model)
            if not sub_provider:
                return instance.response_handler.create_error_response(
                    message='No sub-providers were found for the specified model. Try again later.',
                    status_code=503,
                    error_type='sub_provider_error'
                )

            return await instance.endpoint_handler.handle_moderations(
                request, model, input, sub_provider
            )

        except Exception:
            await instance.endpoint_handler._handle_error(
                request, model, traceback.format_exc()
            )
            return instance.response_handler.create_error_response(
                traceback.format_exc()
            )

    @classmethod
    async def audio_speech(
        cls,
        request: Request,
        model: str,
        input: str,
        **kwargs
    ) -> Response:
        instance = cls()

        try:
            sub_provider = await instance.sub_provider_manager.get_available_provider(model)
            if not sub_provider:
                return instance.response_handler.create_error_response(
                    message='No sub-providers were found for the specified model. Try again later.',
                    status_code=503,
                    error_type='sub_provider_error'
                )

            return await instance.endpoint_handler.handle_audio_speech(
                request, model, input, sub_provider, **kwargs
            )

        except Exception:
            await instance.endpoint_handler._handle_error(
                request, model, traceback.format_exc()
            )
            return instance.response_handler.create_error_response(
                traceback.format_exc()
            )

    @classmethod
    async def audio_transcriptions(
        cls,
        request: Request,
        model: str,
        file: UploadFile
    ) -> PrettyJSONResponse:
        instance = cls()

        try:
            sub_provider = await instance.sub_provider_manager.get_available_provider(model)
            if not sub_provider:
                return instance.response_handler.create_error_response(
                    message='No sub-providers were found for the specified model. Try again later.',
                    status_code=503,
                    error_type='sub_provider_error'
                )

            return await instance.endpoint_handler.handle_audio_transcriptions(
                request, model, file, sub_provider
            )

        except Exception:
            await instance.endpoint_handler._handle_error(
                request, model, traceback.format_exc()
            )
            return instance.response_handler.create_error_response(
                traceback.format_exc()
            )

    @classmethod
    async def audio_translations(
        cls,
        request: Request,
        model: str,
        file: UploadFile
    ) -> PrettyJSONResponse:
        instance = cls()

        try:
            sub_provider = await instance.sub_provider_manager.get_available_provider(model)
            if not sub_provider:
                return instance.response_handler.create_error_response(
                    message='No sub-providers were found for the specified model. Try again later.',
                    status_code=503,
                    error_type='sub_provider_error'
                )

            return await instance.endpoint_handler.handle_audio_translations(
                request, model, file, sub_provider
            )

        except Exception:
            await instance.endpoint_handler._handle_error(
                request, model, traceback.format_exc()
            )
            return instance.response_handler.create_error_response(
                traceback.format_exc()
            )