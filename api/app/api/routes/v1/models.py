from fastapi import APIRouter
from typing import Dict, Any
from ....providers import Model
from ....responses import PrettyJSONResponse

router = APIRouter()

@router.get('', response_class=PrettyJSONResponse)
async def models() -> Dict[str, Any]:
    return {
        'an_easier_overview_available_here': 'https://docs.zukijourney.com/models',
        'object': 'list',
        'data': Model.all_to_json()
    }