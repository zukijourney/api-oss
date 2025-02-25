import os
import inspect
import importlib
from dataclasses import dataclass
from typing import List, Optional, Type, ClassVar, Set, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from asgiref.sync import sync_to_async
from ..core import settings

@dataclass(frozen=True)
class ProviderConfig:
    name: str
    supports_vision: bool = False
    supports_real_streaming: bool = False
    supports_tool_calling: bool = False
    free_models: List[str] = None
    paid_models: List[str] = None
    early_access_models: List[str] = None

    def __post_init__(self):
        for field in ['free_models', 'paid_models', 'early_access_models']:
            object.__setattr__(self, field, getattr(self, field) or [])

    @property
    def all_models(self) -> List[str]:
        return self.free_models + self.paid_models + self.early_access_models

class DatabaseManager:
    def __init__(self, db_url: str):
        try:
            self.client = AsyncIOMotorClient(db_url)
            self.db = self.client['db']['providers']
        except Exception as e:
            raise ConnectionError(f'Database connection failed: {e}')

    async def remove_providers(self, names: Set[str]) -> None:
        for name in names:
            await self.db.delete_one({'name': name})

    async def insert_provider(self, config: ProviderConfig) -> None:
        provider_data = self._create_provider_data(config)
        await self.db.insert_one(provider_data)

    async def update_provider_models(self, config: ProviderConfig, existing_data: Dict[str, Any]) -> None:
        if config.all_models != existing_data['models']:
            await self.db.update_one(
                {'name': config.name},
                {'$set': {'models': config.all_models}}
            )

    def _create_provider_data(self, config: ProviderConfig) -> Dict[str, Any]:
        return {
            'name': config.name,
            'supports_vision': config.supports_vision,
            'supports_real_streaming': config.supports_real_streaming,
            'supports_tool_calling': config.supports_tool_calling,
            'models': config.all_models,
            **self._create_model_metrics(config.all_models)
        }

    def _create_model_metrics(self, models: List[str]) -> Dict[str, Dict[str, int]]:
        return {
            metric: {model: 0 for model in models}
            for metric in ['usage', 'failures', 'latency']
        }

class ModuleLoader:
    @staticmethod
    async def import_modules(cls) -> None:
        @sync_to_async
        def _import_modules():
            root_file = inspect.getfile(cls)
            package_dir = os.path.dirname(root_file)
            base_module = cls.__module__.rsplit('.', 1)[0]

            for root, _, files in os.walk(package_dir):
                for file in [f for f in files if f.endswith('.py') and f != '__init__.py']:
                    ModuleLoader._import_module(root, file, package_dir, base_module)

        await _import_modules()

    @staticmethod
    def _import_module(root: str, file: str, package_dir: str, base_module: str) -> None:
        try:
            rel_path = os.path.relpath(os.path.dirname(os.path.join(root, file)), package_dir)
            module_path = (f'{base_module}.{rel_path.replace(os.sep, ".")}.{os.path.splitext(file)[0]}'
                         if rel_path != '.' else f'{base_module}.{os.path.splitext(file)[0]}')
            importlib.import_module(module_path)
        
        except ImportError as e:
            print(f'Failed to import module {file}: {e}')

class BaseProvider:
    config: ClassVar[ProviderConfig] = ProviderConfig(name='')

    def __init__(self):
        self.db_manager = DatabaseManager(settings.db_url)

    @classmethod
    def get_provider_class(cls, name: str) -> Optional[Type['BaseProvider']]:
        return next(
            (provider for provider in cls.__subclasses__() 
             if provider.config.name == name),
            None
        )

    @classmethod
    def get_all_models(cls) -> Set[str]:
        return {
            model
            for provider in cls.__subclasses__()
            for model in provider.config.all_models
        }

    async def import_modules(self) -> None:
        await ModuleLoader.import_modules(self.__class__)

    async def sync_to_db(self) -> None:
        try:
            existing_providers = await self.db_manager.db.find({}).to_list(length=None)
            existing_names = {p['name'] for p in existing_providers}
            current_names = {p.config.name for p in self.__class__.__subclasses__()}

            await self.db_manager.remove_providers(existing_names - current_names)
            await self._sync_new_providers(current_names - existing_names)
            await self._sync_existing_providers(existing_providers)

        except Exception as e:
            raise RuntimeError(f'Database synchronization failed: {e}')

    async def _sync_new_providers(self, new_names: Set[str]) -> None:
        for name in new_names:
            provider_class = self.get_provider_class(name)
            if provider_class:
                await self.db_manager.insert_provider(provider_class.config)

    async def _sync_existing_providers(self, existing_providers: List[Dict[str, Any]]) -> None:
        for provider_class in self.__class__.__subclasses__():
            config = provider_class.config
            for db_provider in existing_providers:
                if db_provider['name'] == config.name:
                    await self.db_manager.update_provider_models(config, db_provider)