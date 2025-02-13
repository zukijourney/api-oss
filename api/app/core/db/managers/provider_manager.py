from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorClient
from ...config import Settings

settings = Settings()

class ProviderDatabase:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.db_url)
        self.collection = self.client['db']['providers']

class ProviderManager:
    def __init__(self):
        self.db = ProviderDatabase()

    def _calculate_availability(
        self,
        usage: int = 0,
        failures: int = 0
    ) -> float:
        if usage > 0:
            return ((usage - failures) / usage) * 100
        return 100.0 - failures

    def _filter_providers(
        self,
        providers: List[Dict[str, Any]],
        vision: bool = False,
        tools: bool = False,
        excluded_providers: List[str] = []
    ) -> List[Dict[str, Any]]:
        filtered = providers.copy()

        if vision:
            filtered = [p for p in filtered if p['supports_vision']]
        if tools:
            filtered = [p for p in filtered if p['supports_tool_calling']]
        if excluded_providers:
            filtered = [p for p in filtered if p['name'] not in excluded_providers]

        return filtered
    
    async def get_specific_provider(
        self,
        name: str
    ) -> Optional[Dict[str, Any]]:
        return await self.db.collection.find_one({
            'name': name
        })

    async def get_best_provider(
        self,
        model: str,
        vision: bool = False,
        tools: bool = False,
        excluded_providers: List[str] = []
    ) -> Optional[Dict[str, Any]]:
        providers = await self.db.collection.find({
            'models': {'$in': [model]}
        }).to_list(length=None)

        if not providers:
            return None

        filtered_providers = self._filter_providers(
            providers,
            vision=vision,
            tools=tools,
            excluded_providers=excluded_providers
        )

        return min(
            filtered_providers,
            key=lambda x: (
                x['usage'].get(model, 0),
                x['failures'].get(model, 0),
                x['latency_avg'].get(model, 0),
                -self._calculate_availability(
                    x['usage'].get(model, 0),
                    x['failures'].get(model, 0)
                ),
                not x['supports_real_streaming']
            )
        )
    
    async def update_provider(
        self,
        provider_name: str,
        new_data: Dict[str, Any]
    ) -> None:
        update_data = {k: v for k, v in new_data.items() if k != '_id'}
        
        await self.db.collection.update_one(
            filter={'name': provider_name},
            update={'$set': update_data},
            upsert=True
        )