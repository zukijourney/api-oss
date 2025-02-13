import traceback
from discord import Member, Interaction, Embed, ButtonStyle, Color
from discord.ui import View, Button, button
from ..core import UserManager
from ..utils import Utils

class APIControlPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self._db = UserManager()
        self._utils = Utils()

    def _get_user_tier(self, user: Member) -> str:
        tier_roles = {
            'enterprise': 1199051516758200351,
            'onlyfans': 1305748992768086107,
            'subscriber': 1180752369986834492,
            'donor': [1180773896526512138, 1109578498294681601, 1099553128870858783, 1147598405275762688]
        }

        for tier, role_id in tier_roles.items():
            if isinstance(role_id, list):
                if any((role.id in role_id or role.id == role_id) for role in user.roles):
                    return tier
            else:
                if any(role.id == role_id for role in user.roles):
                    return tier

        return 'normal'

    @button(label='Generate Key', style=ButtonStyle.green, custom_id='generate_key')
    async def generate_key(self, interaction: Interaction, _: Button) -> None:
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.guild:
            return await interaction.followup.send('Use this in a server.', ephemeral=True)

        try:
            user = await self._db.get_user(interaction.user.id)

            if not user:
                new_user = await self._db.insert_user(interaction.user.id)
                message = (
                    f'Your key: `{new_user["key"]}`\n'
                    'Important notes:\n'
                    '- API base: api.zukijourney.com/v1\n'
                    '- IP-locked to your first request\'s IP\n'
                    '- Apply for Premium in a ticket\n'
                    '- Read docs: https://docs.zukijourney.com/ai'
                )
                await interaction.followup.send(
                    message, 
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f'Existing key: `{user["key"]}`', 
                    ephemeral=True
                )
        except Exception:
            traceback.print_exc()
            await interaction.followup.send('Key generation error.', ephemeral=True)

    @button(label='View Stats', style=ButtonStyle.blurple, custom_id='view_stats')
    async def view_stats(self, interaction: Interaction, _: Button) -> None:
        await interaction.response.defer(ephemeral=True)
        
        stats = await self._db.get_user(interaction.user.id)

        def format_date(date: float) -> str:
            return f'<t:{int(round(date))}:R>' if date else 'N/A'

        try:
            fields = [
                ('Your Key', f'||{stats.get("key", "Unknown")}||'),
                ('Banned?', stats.get('banned', 'N/A')),
                ('Your IP (IP-Lock for Non-Subscribers)', f'||{stats.get("ip", "No IP locked")}||'),
                ('Credits', stats.get('credits', 'N/A')),
                ('Credits Last Reset (Auto-reset daily on <5k credits)', format_date(stats.get('last_daily'))),
                ('Premium Tier', self._get_user_tier(interaction.user)),
                ('Premium Expiration', format_date(stats.get('premium_expiry')))
            ]

            embed = Embed(title=f'{interaction.user.display_name}\'s API Stats', color=Color.blue())
            for name, value in fields:
                embed.add_field(name=name, value=value, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception:
            await interaction.followup.send('It appears you have no key saved... are you sure you have one?',ephemeral=True)

    @button(label='Reset IP', style=ButtonStyle.grey, custom_id='reset_ip')
    async def reset_ip(self, interaction: Interaction, _: Button) -> None:
        await interaction.response.defer(ephemeral=True)
        user = await self._db.get_user(interaction.user.id)

        if not user:
            return await interaction.followup.send('No API-Key found. Generate one first!', ephemeral=True)

        if user['banned']:
            return await interaction.followup.send('Cannot reset IP when banned.', ephemeral=True)

        user['ip'] = None
        await self._db.update_user(user['user_id'], user)
        await interaction.followup.send('IP reset successful!', ephemeral=True)