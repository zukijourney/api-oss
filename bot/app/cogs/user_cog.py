from discord import Interaction, Member, app_commands
from discord.ext import commands
from typing import Optional
from ..utils import Utils

class UserCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._utils = Utils()

    group = app_commands.Group(name='user', description='...')

    @group.command(name='get-key', description='Generate or get an API key.')
    async def get(self, interaction: Interaction) -> None:
        await self._utils.retrieve_api_key(interaction)

    @group.command(name='lookup', description='Look up an user\'s data.')
    @app_commands.describe(user='[OPTIONAL] The user to lookup.')
    async def lookup(self, interaction: Interaction, user: Optional[Member] = None) -> None:
        await self._utils.user_lookup(interaction, user)
    
    @group.command(name='reset-ip', description='Reset your API key\'s IP.')
    async def reset_ip(self, interaction: Interaction) -> None:
        await self._utils.reset_user_ip(interaction)
    
    @group.command(
        name='nuke',
        description='Switch the ban status of an user.'
    )
    @app_commands.describe(
        user='The user to switch the ban status of.',
        status='The value that determines if an user will be banned or not.'
    )
    async def nuke(
        self,
        interaction: Interaction,
        user: Member,
        status: bool
    ) -> None:
        await self._utils.modify_user_status(
            interaction,
            user,
            'banned',
            status
        )
    
    @group.command(
        name='tier',
        description='Switch the premium tier of an user.'
    )
    @app_commands.choices(
        tier=[
            app_commands.Choice(name='Member', value=0),
            app_commands.Choice(name='Donator/Contributor', value=1),
            app_commands.Choice(name='Subscriber', value=2),
            app_commands.Choice(name='OnlyFans', value=3),
            app_commands.Choice(name='Enterprise', value=4),
            app_commands.Choice(name='Developer/Staff', value=5)
        ]
    )
    @app_commands.describe(
        user='The user to change the premium status.',
        tier='The new tier of the user.',
        months='[OPTIONAL] The amount of months of the premium subscription.'
    )
    async def tier(
        self,
        interaction: Interaction,
        user: Member,
        tier: app_commands.Choice[int],
        months: Optional[int]
    ) -> None:
        await self._utils.modify_user_status(
            interaction,
            user,
            'premium_tier',
            tier.value,
            months
        )

    @group.command(
        name='add-credits',
        description='Add credits to an user\'s API key.'
    )
    @app_commands.describe(
        user='The user to add the credits to.',
        credits='The amount of credits to add to the user.'
    )
    async def add_credits(
        self,
        interaction: Interaction,
        user: Member,
        credits: int
    ) -> None:
        await self._utils.add_credits_to_user(
            interaction,
            user,
            credits
        )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(UserCog(bot))