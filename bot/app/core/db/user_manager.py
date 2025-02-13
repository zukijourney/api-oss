import time
import secrets
import logging
import yaml
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from ..config import settings

class DatabaseError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class UserDatabase:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.db_url)
        self.collection = self.client['db']['users']

class UserManager:
    def __init__(self):
        self._db = UserDatabase()

        try:
            with open('credits.yml', 'r') as config_file:
                self._credits_config = yaml.safe_load(config_file)
        except FileNotFoundError:
            logging.error('Credits configuration file not found: credits.yml')
            self._credits_config = {}
        except yaml.YAMLError as e:
            logging.error(f'Error parsing credits configuration: {e}')
            self._credits_config = {}

    async def get_user(
        self,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        try:
            return await self._db.collection.find_one({'user_id': str(user_id)})
        except Exception as e:
            raise DatabaseError(f'Failed to retrieve user: {str(e)}')

    async def update_user(
        self,
        user_id: int,
        new_data: Dict[str, Any],
        upsert: bool = True
    ) -> Optional[Dict[str, Any]]:
        try:
            update_data = {k: v for k, v in new_data.items() if k != '_id'}
            
            return await self._db.collection.update_one(
                filter={'user_id': str(user_id)},
                update={'$set': update_data},
                upsert=upsert
            )

        except Exception as e:
            raise DatabaseError(f'Failed to update user: {str(e)}')

    async def insert_user(self, id: int) -> Optional[Dict[str, Any]]:
        try:
            insert_data = {
                'user_id': str(id),
                'key': f'zu-{secrets.token_hex(16)}',
                'premium_tier': 0,
                'banned': False,
                'credits': self._credits_config[0],
                'premium_expiry': 0,
                'last_daily': time.time(),
                'ip': None
            }
            await self._db.collection.insert_one(insert_data)
            return insert_data
        except Exception as e:
            raise DatabaseError(f'Failed to insert user: {str(e)}')

    async def delete_user(self, user_id: str) -> None:
        try:
            await self._db.collection.delete_one({'user_id': user_id})
        except Exception as e:
            raise DatabaseError(f'Failed to delete user: {str(e)}')