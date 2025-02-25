import traceback
from fastapi import APIRouter, Request, HTTPException
from .....responses import PrettyJSONResponse
from ....constants import DEPENDENCIES
from .....models import ImageRequest
from .....core import ProviderManager
from .....providers import Model, BaseProvider
from ....exceptions import InsufficientCreditsError, NoProviderAvailableError

router = APIRouter()

class ImageGenerationHandler:
    provider_manager = ProviderManager()

    @classmethod
    async def _get_provider(cls, model: str) -> dict:
        provider = await cls.provider_manager.get_best_provider(model)
        if not provider:
            raise NoProviderAvailableError()
        return provider

    @staticmethod
    def _validate_credits(
        available_credits: int,
        required_tokens: int
    ) -> None:
        if required_tokens > available_credits:
            raise InsufficientCreditsError(
                available_credits=available_credits,
                required_tokens=required_tokens
            )

    @staticmethod
    def _get_token_count(model: str) -> int:
        model_instance = Model.get_model(model)
        return model_instance.pricing.price

@router.post('', dependencies=DEPENDENCIES, response_model=None)
async def images_generations(
    request: Request,
    data: ImageRequest
) -> PrettyJSONResponse:
    try:
        provider = await ImageGenerationHandler._get_provider(data.model)
        provider_instance = BaseProvider.get_provider_class(provider['name'])
        
        token_count = ImageGenerationHandler._get_token_count(
            data.model
        )

        ImageGenerationHandler._validate_credits(
            available_credits=request.state.user['credits'],
            required_tokens=token_count
        )

        request.state.provider = provider
        request.state.provider_name = provider['name']

        return await provider_instance.images_generations(
            request,
            **data.model_dump(mode='json')
        )

    except (InsufficientCreditsError, NoProviderAvailableError) as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=traceback.format_exc()
        )