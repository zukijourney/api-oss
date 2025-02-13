import os
import re
from discord import Intents, TextChannel, Member, Status, CustomActivity
from discord.ext import commands
from .core import UserManager, DatabaseError
from .views import FAQPanel, APIControlPanel, RoleInformationPanel

class DiscordBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=Intents.all()
        )
        self._db = UserManager()

    async def load_cogs(self) -> None:
        for file in os.listdir(os.path.join(os.path.dirname(__file__), 'cogs')):
            if file.endswith('.py') and not file.startswith('_'):
                await self.load_extension(f'app.cogs.{file[:-3]}')
                
    async def setup_hook(self) -> None:
        await self.load_cogs()
        await self.tree.sync()
        print(f'Logged in as {self.user} (ID: {self.user.id})')
    
    async def on_ready(self) -> None:
        self.add_view(APIControlPanel())
        self.add_view(RoleInformationPanel())
        self.add_view(FAQPanel())
        await self.change_presence(
            status=Status.idle,
            activity=CustomActivity('Powering Zukijourney <3')
        )
    
    async def on_member_remove(self, member: Member) -> None:
        try:
            user = await self._db.get_user(member.id)
            if user:
                user['banned'] = True
                user['premium_tier'] = 0
                await self._db.update_user(user['user_id'], user)
        except DatabaseError as e:
            print(f'Error updating user: {e}')

    async def on_guild_channel_create(self, channel: TextChannel):
        if not re.match(r'ticket-[0-9]{4}', channel.name.lower()):
            return

        excluded_roles = {1107751429751459850, 1099553874123165786, 1099553983883923496}
        mentionable_users = [
            member.mention for member in channel.members 
            if not any(role.id in excluded_roles for role in member.roles)
        ]

        mentions_string = ', '.join(mentionable_users)

        crypto_info = [
            'Bitcoin: bc1q65kd9fh93a62cuprdhqts4qzlamm2p9z3cq9h4',
            'Litecoin: ltc1qcgf0ecxjequum2ngrkvannsqd9yf2q5mfwvj7w',
            'Ethereum: 0xf91FF77Cc84A3522EeEda92dBeCD72d829A47b15',
            'Avalanche: 0x03261AD77248f9268CFB09223bE7e1984e44C914',
            'Solana: FeG3sf4e1MxVrBC2zrTJJZBbFcpLAj5z4mdQ7kHGN2CH',
            'Monero: 44f6A9NsuhAYyYLAyznoLa2sniVpLzBrnVsGv3yVb8SN356o1F72tQwUSzvNiSPb7kQaJi4U5BwNmGJSmfawkSEGBKvpCJe',
            'Toncoin: UQAoSUQVmJGrzvrEEoooBuLwdT9kz-m-3OFt85JS5WT-quQZ',
            'Bitcoin Cash: qr3dnv46y37csk70cs3h68ss42smp5l6fydwxgxcng',
            'Tron: TUi2PsNSqPhmXmAJiMkd4RUTXQNJyxsiSc'
        ]

        message = (
            f'Hello {mentions_string} welcome to the tickets channel. '
            'Ask your question and mention me, and I will try to respond to you using my knowledge of '
            'https://docs.zukijourney.com/ai -- if you are unable to get an answer through me, '
            'mention another one of the executives!'
            '\n\nFor Crypto Donations, contact <@881961145236353056> for specifics.'
            '\nZukiJourney supports the following cryptos at least:\n' + 
            '\n'.join(crypto_info)
        )

        await channel.send(message)