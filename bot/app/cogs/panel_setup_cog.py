from discord import Interaction, Embed, Color, app_commands, utils
from discord.ext import commands
from ..views import FAQPanel, APIControlPanel, RoleInformationPanel

class PanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command(name='setup-faq-panel', description='Setup the FAQ panel')
    async def setup_faq(self, interaction: Interaction):
        is_admin = utils.get(interaction.user.roles, name='executives (the c-levels)')

        if not is_admin:
            await interaction.followup.send(
                f'{interaction.user.name} is not in the sudoers file. This incident will be reported.', 
                ephemeral=True
            )
            return

        embed = Embed(
            title='Zukijourney FAQ Hub',
            color=Color.blue(),
            description='\n\n*Select a category below to view detailed answers. All responses are private!*'
        )

        fields = {
            '📡 API & Technical Support': [
                '• API Keys & Access',
                '• IP Locks & Resets',
                '• Credit System',
                '• Model Access',
                '• Error Resolution'
            ],
            '🤖 Bot Features & Usage': [
                '• zuki.gm Optimization',
                '• Context System',
                '• Combat & Difficulty',
                '• Manual Controls',
                '• Time Bot Setup'
            ]
        }

        for name, items in fields.items():
            embed.add_field(
                name=name,
                value='Get help with:\n' + '\n'.join(items),
                inline=True
            )

        await interaction.channel.send(embed=embed, view=FAQPanel())
    
    @app_commands.command(name='setup-api-panel', description='Setup the API control panel')
    async def setup_api_panel(self, interaction: Interaction):
        is_admin = utils.get(interaction.user.roles, name='executives (the c-levels)')

        if not is_admin:
            await interaction.followup.send(
                f'{interaction.user.name} is not in the sudoers file. This incident will be reported.', 
                ephemeral=True
            )
            return

        embed = Embed(
            title='Zukijourney API Control Panel',
            description='\n'.join([
                'Welcome to the Zukijourney API Control Panel!',
                '',
                '🔑 Use the buttons below to manage your API key and account.',
                '📚 Documentation: https://docs.zukijourney.com/ai',
                '❓ Need help? Contact the <@1155955452740370585> bot or open a ticket in <#1099424338287014029>!'
            ]),
            color=Color.blue()
        )
        
        await interaction.channel.send(embed=embed, view=APIControlPanel())
    
    @app_commands.command(name='setup-role-panel', description='Setup the role information panel')
    async def setup_role_panel(self, interaction: Interaction):
        is_admin = utils.get(interaction.user.roles, name='executives (the c-levels)')

        if not is_admin:
            await interaction.followup.send(
                f'{interaction.user.name} is not in the sudoers file. This incident will be reported.', 
                ephemeral=True
            )
            return

        base_info = [
            'Use this panel to explore roles and their benefits! Each button provides detailed information about:',
            '',
            '• Available token amounts',
            '• Model access and restrictions',
            '• API features and limitations',
            '• Bot commands and cooldowns',
            '',
            'Start by checking \'What you currently have now!\' to see your base benefits.',
            '',
            'Looking to upgrade? All paid tiers include:',
            '• Custom AI models (caramelldansen-1 & zukigm-1)',
            '• Premium model access in `/gm` and `/sd`',
            '• IP management options',
            '• Priority support levels',
            '',
            '*Click any button below to learn more!*'
        ]

        embed = Embed(
            title='Welcome to Zukijourney!',
            description='\n'.join(base_info),
            color=Color.blue()
        )

        await interaction.channel.send(embed=embed, view=RoleInformationPanel())

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PanelCog(bot))