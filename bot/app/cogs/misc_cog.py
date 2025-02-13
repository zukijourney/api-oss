import random
from discord import Interaction, app_commands
from discord.ext import commands
from http import HTTPStatus
from typing import Optional, Tuple
from ..core import UserManager

class Utils:
    @staticmethod
    def handle_dice_game(credits: int, bet: int) -> Tuple[int, str]:
        dice_result = random.randint(1, 6)
        won = dice_result >= 4
        new_credits = credits + bet if won else credits - bet
        message = f'🎲 You rolled a {dice_result} and {"won" if won else "lost"}! You now have {new_credits} credits.'
        return new_credits, message

    @staticmethod
    def handle_coin_game(credits: int, bet: int) -> Tuple[int, str]:
        won = random.random() > 0.5
        new_credits = credits + bet if won else credits - bet
        message = f'🪙 You flipped {"heads" if won else "tails"} and {"won" if won else "lost"}!'
        return new_credits, message

    @staticmethod
    def get_http_code_data(status_code: int):
        status_description = HTTPStatus(status_code).description
        status_meaning = HTTPStatus(status_code).phrase
        return (
            f'Status code {status_code} ({status_meaning}): {status_description}\n'
            f'http://http.cat/{status_code}'
        )

class MiscCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def global_cooldown(
        interaction: Interaction
    ) -> Optional[app_commands.Cooldown]:
        if interaction.user.id == 325699845031723010:
            return None

        db = UserManager()
        user = await db.get_user(interaction.user.id)

        if user['credits'] > 0:
            return app_commands.Cooldown(1, 22.0)

        return app_commands.Cooldown(1, 222.0)

    @app_commands.command(
        name='gamble',
        description='Gamble your credits on several games!'
    )
    @app_commands.describe(
        bet='The amount of credits you want to bet.',
        game_type='Choose: dice or coin'
    )
    @app_commands.choices(
        game_type=[
            app_commands.Choice(name='dice', value='dice'),
            app_commands.Choice(name='coin', value='coin')
        ]
    )
    @app_commands.checks.dynamic_cooldown(global_cooldown)
    async def gamble(
        self,
        interaction: Interaction,
        bet: int,
        game_type: app_commands.Choice[str]
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        db = UserManager()
        user = await db.get_user(interaction.user.id)

        if not user.get('credits'):
            await interaction.followup.send('You do not have any credits.', ephemeral=True)
            return

        if bet > user['credits'] or bet <= 0:
            await interaction.followup.send('Invalid bet amount.', ephemeral=True)
            return

        games = {
            'dice': lambda: Utils.handle_dice_game(user['credits'], bet),
            'coin': lambda: Utils.handle_coin_game(user['credits'], bet)
        }
        
        new_credits, message = games[game_type.value]()

        user['credits'] = new_credits
        await db.update_user(user['user_id'], user)

        await interaction.followup.send(message, ephemeral=True)

    @gamble.error
    async def on_error(self, interaction: Interaction, error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f'This command is on cooldown. Please try again in {error.retry_after:.2f} seconds.',
                ephemeral=True
            )
        else:
            raise error

    @app_commands.command(
        name='http-lookup',
        description='Look up an HTTP status code and post its description.',
    )
    @app_commands.describe(
        status_code='The HTTP status code you want to look up.'
    )
    async def http_command(
        self,
        interaction: Interaction,
        status_code: int
    ) -> None:
        await interaction.response.send_message(
            Utils.get_http_code_data(status_code)
        )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MiscCog(bot))