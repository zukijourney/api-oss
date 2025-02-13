from discord import Interaction, Embed, Color, ButtonStyle
from discord.ui import View, Button, button
from typing import Dict, Any

class RoleManager:
    def __init__(self):
        self.roles = {
            'enterprise': {
                'id': 1199051516758200351,
                'name': 'Enterprise Benefits',
                'color': 0x3c00bd,
                'price': '$50/month',
                'how_to_get': [
                    'Monthly donation of $50 via Ko-fi or crypto',
                    'Monthly subscription confirmation in support ticket',
                    'Optional: Custom arrangements discussion'
                ],
                'api_access': {
                    'tokens_per_day': "7_000_000",
                    'messages_per_day': "10_000",
                    'ip_policy': 'IP-free key',
                    'support_level': 'Highest priority'
                },
                'benefits': [
                    'All lower tier perks',
                    'Custom arrangements available',
                    'Direct support access', 
                    'Priority feature requests'
                ]
            },
            'onlyfans': {
                'id': 1305748992768086107,
                'name': 'OnlyFans Tier Benefits',
                'color': 0x0dffeb,
                'price': '$25/month',
                'how_to_get': [
                    'Monthly donation of $25 via Ko-fi or crypto',
                    'Monthly subscription confirmation in support ticket'
                ],
                'api_access': {
                    'tokens_per_day': "3_000_000",
                    'messages_per_day': "4_000",
                    'ip_policy': 'IP-free key',
                    'support_level': 'High priority'
                },
                'benefits': [
                    'All Subscriber perks',
                    '4x higher token limit',
                    'Funny tier name',
                    'Just more tokens!'
                ]
            },
            'subscriber': {
                'id': 1180752369986834492,
                'name': 'Subscriber Benefits',
                'color': 0xffadda,
                'price': '$10/month',
                'how_to_get': [
                    'Monthly donation of $10 via Ko-fi or crypto',
                    'Monthly subscription confirmation in support ticket'
                ],
                'api_access': {
                    'tokens_per_day': "750_000",
                    'messages_per_day': "1_200",
                    'ip_policy': 'IP-free key',
                    'support_level': 'High priority'
                },
                'benefits': [
                    'Higher rate limits',
                    'Early access models',
                    'Premium support channel access'
                ]
            },
            'donator': {
                'id': 1180773896526512138,
                'name': 'Donator Benefits',
                'color': Color.red(),
                'price': '$5 one-time',
                'how_to_get': [
                    'One-time donation of $5 via Ko-fi or crypto',
                    'Server boost',
                    'Open a ticket to claim benefits'
                ],
                'api_access': {
                    'tokens_per_day': "300_000",
                    'messages_per_day': "600",
                    'ip_policy': '1 IP per key',
                    'support_level': 'Medium priority'
                },
                'bot_features': [
                    'Premium model access in /gm',
                    'Premium image generation in /sd',
                    '90% lower command cooldowns'
                ]
            },
            'contributor': {
                'id': 1147598405275762688,
                'name': 'Contributor Benefits',
                'color': 0xa3bd88,
                'price': 'Contribution-based',
                'how_to_get': [
                    'Suggest great ideas',
                    'Help improve bot/system',
                    'Open a ticket to discuss contributions'
                ],
                'benefits': [
                    'All Donator perks',
                    'Special role above bots',
                    'Staff groupchat access (depends on contribution)'
                ]
            },
            'booster': {
                'id': 1109578498294681601,
                'name': 'Booster Benefits',
                'color': Color.purple(),
                'price': 'Server Boost',
                'how_to_get': [
                    'Boost the Discord server'
                ],
                'benefits': [
                    'Equivalent to Donator perks while boost is active'
                ]
            },
            'member': {
                'id': None,
                'name': 'Member Benefits',
                'color': Color.blue(),
                'api_access': {
                    'tokens_per_day': "42_069",
                    'messages_per_day': "200",
                    'ip_policy': '1 IP per key'
                },
                'model_access': [
                    'Access to all free models',
                    'caramelldansen-1 (basic model)'
                ],
                'benefits': [
                    'Basic command access',
                    'Public channels',
                    'Daily token refreshes'
                ]
            }
        }

    def create_role_embed(self, role_info: Dict[str, Any]) -> Embed:
        embed = Embed(
            title=role_info['name'], 
            color=role_info.get('color', Color.blue()),
            description=f'Price: {role_info.get("price", "Free")}'
        )
        
        embed_fields = [
            ('how_to_get', 'How to Get'),
            ('benefits', 'Benefits'),
            ('bot_features', 'Bot Features'),
            ('model_access', 'Model Access')
        ]
        
        for key, field_name in embed_fields:
            if key in role_info:
                embed.add_field(
                    name=field_name, 
                    value='\n'.join(f'• {item}' for item in role_info[key]), 
                    inline=False
                )
        
        if 'api_access' in role_info:
            api_details = role_info['api_access']
            embed.add_field(
                name='API Access', 
                value='\n'.join(f'• {k.replace("_", " ").title()}: {v}' for k, v in api_details.items()), 
                inline=False
            )
        
        return embed

class RoleButton(Button):
    def __init__(self, role_manager: RoleManager, role_key: str, *args, **kwargs):
        super().__init__(custom_id=f'{role_key}_role', *args, **kwargs)
        self.role_manager = role_manager
        self.role_key = role_key

    async def callback(self, interaction: Interaction):
        embed = self.role_manager.create_role_embed(self.role_manager.roles.get(self.role_key))
        await interaction.response.send_message(embed=embed, ephemeral=True)

class RoleInformationPanel(View, RoleManager):
    def __init__(self):
        View.__init__(self, timeout=None)
        RoleManager.__init__(self)
        self.setup_buttons()

    def setup_buttons(self) -> None:
        roles = [
            ('Enterprise Tier', ButtonStyle.blurple, 'enterprise'),
            ('OnlyFans Tier', ButtonStyle.blurple, 'onlyfans'),
            ('Subscriber Benefits', ButtonStyle.red, 'subscriber'),
            ('Donator Perks', ButtonStyle.red, 'donator'),
            ('Contributor Benefits', ButtonStyle.green, 'contributor')
        ]
        
        for label, style, role_key in roles:
            self.add_item(RoleButton(self, role_key=role_key, label=label, style=style))

    @button(label='What you currently have now!', style=ButtonStyle.grey, custom_id='member_info')
    async def member_benefits(self, interaction: Interaction, _: Button):
        member_roles = {role.id for role in interaction.user.roles}
        
        highest_role = next(
            (role_info for role_info in self.roles.values() 
             if role_info.get('id') in member_roles), 
            self.roles['member']
        )
        
        embed = self.create_role_embed(highest_role)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(label='How to Donate', style=ButtonStyle.green, custom_id='donation_info')
    async def donation_info(self, interaction: Interaction, _: Button):
        embed = Embed(title='How to Support Zukijourney', color=Color.greyple())
        
        embed.add_field(
            name='Payment Methods', 
            value='• Ko-fi: https://ko-fi.com/zukixa\n• Crypto: Open ticket in <#1099424338287014029>\n  (All Coinbase-supported cryptocurrencies accepted)', 
            inline=False
        )
        
        embed.add_field(
            name='Important Notes', 
            value=(
                '• Open ticket in <#1099424338287014029> to claim perks after donating\n'
                '• Monthly subscribers: Confirm subscription monthly in support ticket (Ko-fi limitation)\n'
                '• Enterprise users: Optional custom arrangements available\n'
                '• Server boosters receive donator perks while boost is active\n'
                '• Roles stack - higher tiers include all lower tier benefits'
            ), 
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)