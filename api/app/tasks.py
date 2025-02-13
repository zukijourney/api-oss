import asyncio
import time
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from .core import settings

@dataclass
class CreditsConfig:
    max_credits: int = 5000
    check_interval: int = 60
    daily_interval: int = 86400
    credits_file: str = 'credits.yml'

class CreditsManager:
    def __init__(
        self,
        db_collection: AsyncIOMotorCollection,
        config: Optional[CreditsConfig] = None
    ):
        self.db = db_collection
        self.config = config or CreditsConfig()
        self.credits_tiers = self._load_credits_tiers()
        
    def _load_credits_tiers(self) -> Dict[int, int]:
        try:
            credits_path = Path(self.config.credits_file)
            if not credits_path.exists():
                raise FileNotFoundError(
                    f'Credits file not found: {self.config.credits_file}'
                )
            
            with credits_path.open() as f:
                return yaml.safe_load(f)

        except Exception as e:
            raise RuntimeError(f'Failed to load credits configuration: {str(e)}')

    async def _get_users_needing_update(self) -> AsyncIOMotorCollection:
        current_time = time.time()
        return self.db.find({
            'credits': {'$lt': self.config.max_credits},
            'last_daily': {
                '$lte': current_time - self.config.daily_interval
            }
        })

    async def _update_user_credits(self, user: Dict[str, Any]) -> None:
        try:
            if user['credits'] >= self.config.max_credits:
                return
            
            new_credits = user['credits'] + self.credits_tiers[user['premium_tier']]

            await self.db.update_one(
                {'user_id': user['user_id']},
                {
                    '$set': {
                        'credits': new_credits,
                        'last_daily': time.time()
                    }
                }
            )

        except Exception as e:
            print(f'Failed to update credits for user {user["user_id"]}: {str(e)}')

    async def process_credits_updates(self) -> None:
        try:
            async for user in await self._get_users_needing_update():
                await self._update_user_credits(user)
        except Exception as e:
            print(f'Error processing credits updates: {str(e)}')

    async def start_credits_service(self) -> None:
        while True:
            try:
                await self.process_credits_updates()
                await asyncio.sleep(self.config.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f'Credits service error: {str(e)}')
                await asyncio.sleep(self.config.check_interval)

class CreditsService:
    def __init__(self):
        self.db = AsyncIOMotorClient(settings.db_url)['db']['users']
        self.config = CreditsConfig()
        self.manager = CreditsManager(self.db, self.config)
        self.task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        if not self.task or self.task.done():
            self.task = asyncio.create_task(
                self.manager.start_credits_service()
            )
    
    async def stop(self) -> None:
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass