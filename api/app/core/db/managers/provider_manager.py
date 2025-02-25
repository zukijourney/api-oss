import random
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any, Optional, List, Tuple
from ...config import Settings

settings = Settings()

class ProviderDatabase:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.db_url)
        self.collection = self.client['db']['providers']

class ProviderManager:
    def __init__(self):
        self.db = ProviderDatabase()
        self.window_size = timedelta(hours=24)
        self.max_usage_ratio = 1

    def _calculate_health_score(
        self,
        provider: Dict[str, Any],
        model: str,
        current_time: datetime,
        total_requests: int
    ) -> float:
        recent_usage = provider.get('usage_history', {}).get(model, [])
        recent_usage = [
            u for u in recent_usage 
            if u['timestamp'] >= current_time - self.window_size
        ]
        
        if not recent_usage:
            return 0.8
            
        provider_requests = sum(u['count'] for u in recent_usage)
        provider_failures = sum(u['failures'] for u in recent_usage)
        avg_latency = sum(u['latency'] * u['count'] for u in recent_usage) / provider_requests
        
        reliability = 1.0 if provider_requests == 0 else (provider_requests - provider_failures) / provider_requests
        latency_score = max(0, 1 - (avg_latency / 2000))
        usage_ratio = provider_requests / max(1, total_requests)
        
        usage_penalty = max(0, 1 - (usage_ratio / self.max_usage_ratio))
        
        weights = {
            'reliability': 0.4,
            'latency': 0.3,
            'usage_penalty': 0.3
        }
        
        return (
            reliability * weights['reliability'] +
            latency_score * weights['latency'] +
            usage_penalty * weights['usage_penalty']
        )

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

    def _select_provider_weighted(
        self,
        providers: List[Tuple[Dict[str, Any], float]]
    ) -> Dict[str, Any]:
        total_score = sum(score for _, score in providers)
        if total_score == 0:
            return random.choice([p for p, _ in providers])
            
        r = random.uniform(0, total_score)
        current_sum = 0
        
        for provider, score in providers:
            current_sum += score
            if current_sum >= r:
                return provider
                
        return providers[-1][0]

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
        current_time = datetime.utcnow()
        
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

        if not filtered_providers:
            return None

        total_requests = 0
        for provider in filtered_providers:
            recent_usage = provider.get('usage_history', {}).get(model, [])
            recent_usage = [
                u for u in recent_usage 
                if u['timestamp'] >= current_time - self.window_size
            ]
            total_requests += sum(u['count'] for u in recent_usage)

        provider_scores = [
            (provider, self._calculate_health_score(
                provider, 
                model, 
                current_time,
                total_requests
            ))
            for provider in filtered_providers
        ]
        
        return self._select_provider_weighted(provider_scores)

    async def update_provider(
        self,
        provider_name: str,
        new_data: Dict[str, Any],
        model: str = None
    ) -> None:
        if model and ('usage' in new_data or 'failures' in new_data or 'latency' in new_data):
            history_entry = {
                'timestamp': datetime.utcnow(),
                'count': new_data.get('usage', {}).get(model, 0),
                'failures': new_data.get('failures', {}).get(model, 0),
                'latency': new_data.get('latency', {}).get(model, 0)
            }
            
            provider = await self.get_specific_provider(provider_name)
            
            if not provider:
                update_data = {k: v for k, v in new_data.items() if k != '_id'}
                update_data['usage_history'] = {model: [history_entry]}
                await self.db.collection.update_one(
                    filter={'name': provider_name},
                    update={'$set': update_data}
                )
            else:
                usage_history = provider.get('usage_history', {})
                model_history = usage_history.get(model, [])
                model_history.insert(0, history_entry)
                usage_history[model] = model_history[:1000]
                
                update_data = {k: v for k, v in new_data.items() if k != '_id'}
                update_data['usage_history'] = usage_history
                
                await self.db.collection.update_one(
                    filter={'name': provider_name},
                    update={'$set': update_data}
                )
        else:
            update_data = {k: v for k, v in new_data.items() if k != '_id'}
            await self.db.collection.update_one(
                filter={'name': provider_name},
                update={'$set': update_data}
            )