from .core import settings
from .main import DiscordBot

DiscordBot().run(settings.token)