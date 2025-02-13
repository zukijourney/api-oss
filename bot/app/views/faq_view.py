from discord import Interaction, Embed, SelectOption, Color
from discord.ui import Select, View

class FAQSelect(Select):
    def __init__(self, faq_type: str):
        self.faq_type = faq_type
        options = self._get_options(faq_type)
        super().__init__(
            placeholder=f'{"📡" if faq_type == "api" else "🤖"} {"API" if faq_type == "api" else "Bot"} Questions...',
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f'{faq_type}_faq_select'
        )

    def _get_options(self, faq_type: str):
        faq_configs = {
            'api': [
                {'label': 'How to Get an API Key', 'description': 'Getting started with your API key', 'emoji': '🔑'},
                {'label': 'Understanding IP Locks', 'description': 'IP restrictions and how to manage them', 'emoji': '🔒'},
                {'label': 'Claiming Donation Benefits', 'description': 'How to get your roles and perks', 'emoji': '⭐'},
                {'label': 'Where to Use the API', 'description': 'Recommended platforms and UIs', 'emoji': '🌐'},
                {'label': 'Model Access Issues', 'description': 'Understanding model availability', 'emoji': '🤖'},
                {'label': 'API Error Troubleshooting', 'description': 'Resolving common errors', 'emoji': '⚠️'}
            ],
            'bot': [
                {'label': 'zuki.gm: Improving Responses', 'description': 'Making the bot more accurate', 'emoji': '🎯'},
                {'label': 'zuki.gm: Context System', 'description': 'Using context for better results', 'emoji': '📝'},
                {'label': 'zuki.gm: Difficulty Settings', 'description': 'Adjusting bot harshness', 'emoji': '⚔️'},
                {'label': 'zuki.gm: Combat Improvement', 'description': 'Better military/combat responses', 'emoji': '🎮'},
                {'label': 'zuki.gm: Manual Corrections', 'description': 'Using /approve for refinements', 'emoji': '✅'},
                {'label': 'zuki.time: Troubleshooting', 'description': 'Common time bot issues', 'emoji': '⏰'},
                {'label': 'zuki.time: Date Limitations', 'description': 'Understanding year restrictions', 'emoji': '📅'}
            ]
        }
        return [SelectOption(**option) for option in faq_configs[faq_type]]

    async def callback(self, interaction: Interaction):
        embed = Embed(color=Color.blue() if self.faq_type == 'api' else Color.green())
        
        faq_details = {
            'api': {
                'How to Get an API Key': {
                    'title': '🔑 Getting Your API Key',
                    'description': (
                        'There are two ways to generate your API key:\n\n'
                        '**Option 1: Using Commands**\n'
                        '• Use `/user key-get` command\n'
                        '**Option 2: Using Control Panel**\n'
                        '• Go to <#1305777445852545024>\n'
                        '• Find the Zukijourney API control panel\n'
                        '• Click \'Generate Key\'\n\n'
                        'Both methods work exactly the same way!'
                    )
                },
                'Understanding IP Locks': {
                    'title': '🔒 IP Lock System',
                    'description': (
                        '**What is IP Lock?**\n'
                        'For free users, donators, contributors, and boosters, your API key is locked to one IP address at a time.\n\n'
                        '**How to Change IP:**\n'
                        '1. Use `/user resetip` command, OR\n'
                        '2. Use the Reset IP button in <#1305777445852545024>\n\n'
                        '**Important Notes:**\n'
                        '• After reset, your next API request sets the new IP\n'
                        '• Automation of IP resets is forbidden and will result in a ban\n'
                        '• Subscriber tier and above are IP-free'
                    )
                },
                'Claiming Donation Benefits': {
                    'title': '⭐ Claiming Donation Benefits',
                    'description': (
                        '**Automatic Process:**\n'
                        '• Claim your donation role directly on Ko-fi\n'
                        '• Perks should activate within ~15 minutes\n\n'
                        '**If Automatic Process Fails:**\n'
                        '• Go to <#1099424338287014029>\n'
                        '• Ping staff member\n'
                        '• Provide proof of donation\n'
                        '• Staff will manually assign role & perks\n\n'
                        'Make sure to keep your donation proof handy!'
                    )
                },
                'Where to Use the API': {
                    'title': '🌐 Using Your API Key',
                    'description': (
                        '**Recommended Platforms:**\n\n'
                        '**Simple Chat Interfaces:**\n'
                        '• https://docs.zukijourney.com/playground - Our basic UI\n'
                        '• https://bettergpt.chat/ - Clean and simple\n\n'
                        '**Advanced Interfaces:**\n'
                        '• https://lobechat.com/chat - Feature-rich UI\n'
                        '• https://librechat.ai/ - For self-hosting\n\n'
                        'All platforms use standard OpenAI format!'
                    )
                },
                'Model Access Issues': {
                    'title': '🤖 Model Access Guide',
                    'description': (
                        '**Checking Model Availability:**\n'
                        '• Visit https://api.zukijourney.com/v1/models\n'
                        '• Or visit https://docs.zukijourney.com/models\n'
                        '• Look for these flags:\n'
                        '  \- `is_free: True` - Available to all\n'
                        '  \- `early_access: True` - Subscriber+ only\n\n'
                        '**Common Issues:**\n'
                        '• Paid but no access? Check if model is early access\n'
                        '• Need early access? Upgrade to Subscriber tier'
                    )
                },
                'API Error Troubleshooting': {
                    'title': '⚠️ API Error Resolution',
                    'description': (
                        '**For \'500 Internal Server Error\':**\n'
                        'Please provide detailed error information:\n'
                        '• Use Chrome\'s Network tab\n'
                        '• Copy full error message\n'
                        '• Include request details\n\n'
                        '**When Reporting Issues:**\n'
                        '• Share complete error messages\n'
                        '• Provide request context\n'
                        '• Include timestamp of error\n\n'
                        'Generic \'it doesn\'t work\' reports cannot be investigated!'
                    )
                }
            },
            'bot': {
                'zuki.gm: Improving Responses': {
                    'title': '🎯 Making zuki.gm More Accurate',
                    'description': (
                        '**Key Elements for Better Responses:**\n\n'
                        '1. **Use Context Fields in** `/gm`:\n'
                        '• Fill out `context`\n'
                        '• Include `visual_context`\n'
                        '• Provide `previous` information\n\n'
                        '2. **Server Setup:**\n'
                        '• Use `/settings task:Add/Override Server-Context`\n'
                        '• Configure `/rag_info` system\n\n'
                        '3. **Fine-tuning:**\n'
                        '• Use `/approve` for manual adjustments\n'
                        '• Provide detailed scenarios'
                    )
                },
                'zuki.gm: Context System': {
                    'title': '📝 Understanding Context System',
                    'description': (
                        '**Essential Setup:**\n'
                        '• Use `/settings task:Add/Override Server-Context`\n'
                        '• Configure `/rag_info` system\n\n'
                        '**For Each Command:**\n'
                        '• Provide detailed context\n'
                        '• Include visual descriptions\n'
                        '• Reference previous interactions\n\n'
                        'The more context provided, the better the responses!'
                    )
                },
                'zuki.gm: Difficulty Settings': {
                    'title': '⚔️ Adjusting Bot Harshness',
                    'description': (
                        '**Changing Difficulty:**\n'
                        '• Use `/settings task:Harshness`\n'
                        '• Default setting is \'easy\'\n'
                        '• Higher difficulty = harsher responses\n\n'
                        '**Note:**\n'
                        'If still not harsh enough after maximum setting,\n'
                        'please provide feedback to staff!'
                    )
                },
                'zuki.gm: Combat Improvement': {
                    'title': '🎮 Enhancing Combat Responses',
                    'description': (
                        '**For Better Military/Combat Responses, Include:**\n'
                        '• Equipment sheets\n'
                        '• Current battle plans\n'
                        '• War territory status\n'
                        '• Tactical maps\n'
                        '• Unit compositions\n\n'
                        '**Remember:**\n'
                        '• More detailed context = better responses\n'
                        '• Use `/approve` for tactical adjustments\n'
                        '• Keep information organized and clear'
                    )
                },
                'zuki.gm: Manual Corrections': {
                    'title': '✅ Using Manual Corrections',
                    'description': (
                        '**The** `/approve` **Command:**\n'
                        '• Allows gamemaster modifications\n'
                        '• Helps refine edge cases\n'
                        '• Provides extra context for corrections\n\n'
                        '**Best Practices:**\n'
                        '• Clearly state what was missed\n'
                        '• Provide reasoning for changes\n'
                        '• Use for fine-tuning responses'
                    )
                },
                'zuki.time: Troubleshooting': {
                    'title': '⏰ zuki.time Troubleshooting',
                    'description': (
                        '**If Time Isn\'t Running:**\n\n'
                        '1. Check your setup:\n'
                        '• Use `/time-info`\n'
                        '• Verify all settings\n\n'
                        '2. If settings look correct but issues persist:\n'
                        '• Take a screenshot of `/time-info`\n'
                        '• Report to staff with the screenshot\n\n'
                        'Most issues are setup-related and can be easily fixed!'
                    )
                },
                'zuki.time: Date Limitations': {
                    'title': '📅 Date Range Limitations',
                    'description': (
                        '**Year Restrictions:**\n'
                        '• Minimum year: 2\n'
                        '• Maximum year: 5000\n\n'
                        '**Technical Reason:**\n'
                        'This is a Python datetime limitation.\n'
                        'See: https://docs.python.org/3/library/datetime.html#datetime.MINYEAR\n\n'
                        'These limitations cannot be changed!'
                    )
                }
            }
        }

        selected_option = self.values[0]
        faq_info = faq_details[self.faq_type].get(selected_option, {})
        
        embed.title = faq_info.get('title', 'FAQ Details')
        embed.description = faq_info.get('description', 'No details available.')

        await interaction.response.send_message(embed=embed, ephemeral=True)

class FAQPanel(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FAQSelect('api'))
        self.add_item(FAQSelect('bot'))