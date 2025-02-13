from fastapi import APIRouter
from typing import Dict, Any
from ...responses import PrettyJSONResponse

router = APIRouter()

@router.get('/', response_class=PrettyJSONResponse)
async def home() -> Dict[str, Any]:
    return {
        'message': 'Welcome to the Zukijourney API! Documentation is available at https://docs.zukijourney.com'
    }