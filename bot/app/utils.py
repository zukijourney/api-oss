import yaml
import time
import logging
from discord import Interaction, Member, HTTPException, InteractionResponded, utils, Embed, Color
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any, Union
from .core import UserManager

class Utils:
    def __init__(self):
        self._db = UserManager()

        try:
            with open('credits.yml', 'r') as config_file:
                self._credits_config = yaml.safe_load(config_file)
        except FileNotFoundError:
            logging.error('Credits configuration file not found: credits.yml')
            self._credits_config = {}
        except yaml.YAMLError as e:
            logging.error(f'Error parsing credits configuration: {e}')
            self._credits_config = {}
    
    async def retrieve_api_key(self, interaction: Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            
            user = await self._db.get_user(interaction.user.id)

            if user:
                await interaction.followup.send(
                    f'Your existing API key is: {user["key"]}', 
                    ephemeral=True
                )
                return
            
            new_user = await self._db.insert_user(interaction.user.id)

            await interaction.followup.send(
                f'Your new API key is: {new_user["key"]}', 
                ephemeral=True
            )
        
        except (HTTPException, InteractionResponded) as e:
            logging.error(f'Error retrieving API key: {e}')
            await interaction.followup.send(
                'An error occurred while processing your request.', 
                ephemeral=True
            )
    
    async def reset_user_ip(self, interaction: Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            
            user = await self._db.get_user(interaction.user.id)

            if not user:
                await interaction.followup.send(
                    'You do not have an existing API key.', 
                    ephemeral=True
                )
                return
            
            user['ip'] = None
            await self._db.update_user(user['user_id'], user)

            await interaction.followup.send(
                f'Successfully reset the IP for {interaction.user.mention}.', 
                ephemeral=True
            )
        
        except (HTTPException, InteractionResponded) as e:
            logging.error(f'Error resetting user IP: {e}')
            await interaction.followup.send(
                'An error occurred while resetting your IP.', 
                ephemeral=True
            )
    
    async def user_lookup(self, interaction: Interaction, member: Optional[Member] = None) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            is_admin = utils.get(interaction.user.roles, name='executives (the c-levels)')
            target_user_id = member.id if member and is_admin else interaction.user.id

            if member and not is_admin:
                await interaction.followup.send(
                    f'{interaction.user.name} is not in the sudoers file. This incident will be reported.', 
                    ephemeral=True
                )
                return

            user = await self._db.get_user(target_user_id)

            if not user:
                await interaction.followup.send(
                    'No API key found for this user.', 
                    ephemeral=True
                )
                return
            
        #    if user.get('banned', False):
         #       await interaction.followup.send(
          #          'This user\'s API key has been banned.', 
           #         ephemeral=True
            #    )
           #     return

            stats = await self._db.get_user(target_user_id)
            
            if isinstance(stats, str):
                await interaction.followup.send(stats, ephemeral=True)
                return

            can_do_daily = False
            reset_string = stats.get('last_daily')

            if reset_string:
                try:
                    reset_time = datetime.fromtimestamp(reset_string)
                    can_do_daily = (datetime.utcnow() - reset_time) > timedelta(hours=24)
                except (ValueError, IndexError):
                    can_do_daily = False

            def format_date(date: float) -> str:
                return f'<t:{int(round(date))}:R>' if date else 'N/A'

            tier_map = {
                0: 'Member',
                1: 'Donator/Contributor',
                2: 'Subscriber',
                3: 'OnlyFans',
                4: 'Enterprise',
                5: 'Developer'
            }
            fields = [
                ('User ID', str(target_user_id)),
                ('Your Key', f'||{stats.get("key", "??? How")}||'),
                ('Banned?', stats.get('banned')),
                ('Your IP', f'||{stats.get("ip", "No IP locked onto at this time.")}|| (Remember, `/user resetip` to reset the ip! (Subscribers & higher dont have to...))'),
                ('Credits', stats.get('credits', 'N/A')),
                ('Credits Last Reset', format_date(reset_string)),
                ('24hrs passed (Credit Reset Due @ <5k credits)?', 'Yes' if can_do_daily else 'No'),
                ('Premium Tier', tier_map.get(stats.get('premium_tier', 0), 'Custom')),
                ('Premium Expiration', 'N/A' if stats.get('premium_tier', 0) <= 1 else format_date(stats.get('premium_expiry')))
            ]

            target_name = member.display_name if member else interaction.user.display_name
            embed = Embed(title=f'{target_name}\'s Detailed Stats', color=Color.blue())

            for name, value in fields:
                embed.add_field(name=name, value=value, inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except (HTTPException, InteractionResponded) as e:
            logging.error(f'Error during user lookup: {e}')
            await interaction.followup.send(
                'An error occurred during user lookup.', 
                ephemeral=True
            )
    
    async def modify_user_status(
        self, 
        interaction: Interaction, 
        member: Member, 
        property_name: str, 
        new_status: Union[str, int],
        months: Optional[int] = None
    ) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            if not utils.get(interaction.user.roles, name='executives (the c-levels)'):
                await interaction.followup.send(
                    f'{interaction.user.name} is not in the sudoers file. This incident will be reported.', 
                    ephemeral=True
                )
                return

            user = await self._db.get_user(member.id)

            if not user:
                await interaction.followup.send(
                    'No API key found for this user.', 
                    ephemeral=True
                )
                return

            if property_name == 'banned':
                await self._handle_ban_modification(
                    interaction, member, new_status
                )
            elif property_name == 'premium_tier':
                await self._handle_premium_modification(
                    interaction, member, user, new_status, months
                )
        
        except (HTTPException, InteractionResponded) as e:
            logging.error(f'Error modifying user status: {e}')
            await interaction.followup.send(
                'An error occurred while modifying user status.', 
                ephemeral=True
            )

    async def add_credits_to_user(
        self, 
        interaction: Interaction, 
        member: Member,
        credits: int
    ) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            if not utils.get(interaction.user.roles, name='executives (the c-levels)'):
                await interaction.followup.send(
                    f'{interaction.user.name} is not in the sudoers file. This incident will be reported.', 
                    ephemeral=True
                )
                return

            user = await self._db.get_user(member.id)

            if not user:
                await interaction.followup.send(
                    'No API key found for this user.', 
                    ephemeral=True
                )
                return

            user['credits'] += credits
            await self._db.update_user(user['user_id'], user)

            await interaction.followup.send(
                f'Successfully added {credits} credits to {member.mention}.', 
                ephemeral=True
            )
        
        except (HTTPException, InteractionResponded) as e:
            logging.error(f'Error modifying user status: {e}')
            await interaction.followup.send(
                'An error occurred while modifying user status.', 
                ephemeral=True
            )
    
    async def _handle_ban_modification(
        self, 
        interaction: Interaction, 
        member: Member, 
        new_status: bool
    ) -> None:
        await self._db.update_user(
            member.id, {'banned': new_status}
        )

        status_message = (
            f'Successfully {"banned" if new_status else "unbanned"} '
            f'{member.mention}.'
        )
        await interaction.followup.send(status_message)
    
    async def _handle_premium_modification(
        self, 
        interaction: Interaction, 
        member: Member, 
        user: Dict[str, Any], 
        premium_tier: int,
        months: Optional[int]
    ) -> None:
        user['premium_tier'] = premium_tier

        if premium_tier > 0:
            user['credits'] += self._credits_config.get(premium_tier, 0)
            current_time = datetime.fromtimestamp(time.time())
            user['last_daily'] = time.time()

            if premium_tier > 1:
                expiry_date = current_time + relativedelta(months=months or 1)
                user['premium_expiry'] = int(expiry_date.timestamp())

        await self._db.update_user(user['user_id'], user)
        
        status_message = (
            f'Successfully set the premium tier '
            f'of {member.mention} to {premium_tier}. '
        )

        if premium_tier > 1:
            status_message += f'\nValid until <t:{int(expiry_date.timestamp())}:R>.'

        tier_roles = {
            4: 1199051516758200351,
            3: 1305748992768086107,
            2: 1180752369986834492,
            1: 1180773896526512138
        }

        if premium_tier in tier_roles:
            roles_to_add = [
                interaction.guild.get_role(tier_roles[premium_tier])
                for tier in range(1, premium_tier + 1)
            ]

            for role in roles_to_add:
                if role:
                    await member.add_roles(role)

        await interaction.followup.send(status_message,ephemeral=False)