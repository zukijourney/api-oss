import traceback
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from typing import Union, Dict, List, Any
from .....responses import PrettyJSONResponse
from ....constants import DEPENDENCIES
from .....models import ChatRequest, Message
from .....utils import RequestProcessor
from .....core import ProviderManager
from .....providers import BaseProvider
from ....exceptions import InsufficientCreditsError, NoProviderAvailableError

router = APIRouter()

request_processor = RequestProcessor()

class ChatCompletionsHandler:
    provider_manager = ProviderManager()

    @staticmethod
    def _has_vision_requirement(messages: List[Message]) -> bool:
        return any(
            isinstance(message.content, list) and 
            any(content.type == 'image_url' for content in message.content)
            for message in messages
        )

    @staticmethod
    def _validate_credits(available_credits: int, required_tokens: int) -> None:
        if required_tokens > available_credits:
            raise InsufficientCreditsError(
                available_credits=available_credits,
                required_tokens=required_tokens
            )

    @classmethod
    async def _get_provider(
        cls,
        model: str = '',
        vision_required: bool = False,
        tools_required: bool = False,
        name: str = ''
    ) -> Dict[str, Any]:
        if name:
            provider = await cls.provider_manager.get_specific_provider(name)
        else:
            provider = await cls.provider_manager.get_best_provider(
                model=model,
                vision=vision_required,
                tools=tools_required
            )

        if not provider:
            print(f'{model}: No provider available')
            raise NoProviderAvailableError()

        return provider

@router.post('', dependencies=DEPENDENCIES, response_model=None)
async def chat_completions(
    request: Request,
    data: ChatRequest
) -> Union[PrettyJSONResponse, StreamingResponse]:
    try:
        token_count = request_processor.count_tokens(data)
        
        ChatCompletionsHandler._validate_credits(
            available_credits=request.state.user['credits'],
            required_tokens=token_count
        )
        request.state.token_count = token_count

        if data.provider_name and request.state.user.get('premium_tier', 0) == 5:
            provider = await ChatCompletionsHandler._get_provider(
                model=data.model,
                name=data.provider_name
            )
        else:
            vision_required = ChatCompletionsHandler._has_vision_requirement(data.messages)
            provider = await ChatCompletionsHandler._get_provider(
                model=data.model,
                vision_required=vision_required,
                tools_required=data.tools
            )
        
        request.state.provider = provider
        request.state.provider_name = provider['name']

        provider_instance = BaseProvider.get_provider_class(provider['name'])

        if not provider_instance:
            raise HTTPException(
                status_code=500,
                detail=(
                    'Something went wrong when getting the provider class, '
                    'which turned out to be null. Please try again later.'
                )
            )

        response = await provider_instance.chat_completions(
            request,
            **data.model_dump(
                mode='json',
                exclude_none=True,
                exclude={'provider_name'}
            )
        )

        if response.status_code == 503:
            print(f'{data.model}: No sub-provider available ({provider["name"]})')

        return response
        
    except (InsufficientCreditsError, NoProviderAvailableError) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=traceback.format_exc()
        )