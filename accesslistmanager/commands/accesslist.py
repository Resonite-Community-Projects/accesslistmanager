import traceback
import asyncio
import time

import disnake
from disnake.ext import commands
from resonitepy.exceptions import InvalidToken, ResoniteAPIException

from accesslistmanager.config import RESONITE_PASSWORD, RESONITE_USERNAME, RESONITE_VAR_GROUP, RESONITE_VAR_PATH, DISCORD_LOG_OUTPUT_CHANNEL
from accesslistmanager.logger import am_logger, usage_logger
from accesslistmanager.models import Session, User
from accesslistmanager.utils import login

db_session = Session()

RESONITE_VAR_GROUP = RESONITE_VAR_GROUP[:22]
async def autocomp_members(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if user_input.startswith('U-'):
        members = db_session.query(User).filter(User.resonite_username.startswith(user_input)).all()
        members = [member.resonite_username for member in members]
    elif len(user_input) > 1:
        members = inter.guild.members
        members = [f"{member.name}#{member.discriminator}" for member in members if member.name.startswith(user_input)]
    else:
        members = db_session.query(User).filter(User.resonite_username.startswith(user_input)).all()
        members = [member.resonite_username for member in members]
        _members = inter.guild.members
        members.extend([f"{member.name}#{member.discriminator}" for member in _members if member.name.startswith(user_input)])
    return members[:25]

async def autocomp_discord_members(inter: disnake.ApplicationCommandInteraction, user_input: str):
    members = inter.guild.members
    members = [f"{member.name}#{member.discriminator}" for member in members if member.name.startswith(user_input)]
    return members[:25]


class AccessList(commands.Cog):

    def __init__(self, bot, db_session, resonite_client):
        self.bot = bot
        self.db_session = db_session
        self.resonite_client = resonite_client

    @commands.slash_command(description='Manage accesslist')
    async def accesslist(self, inter):
        pass

    @accesslist.sub_command(name='add', description='Adds a new users to the cloud variable')
    async def add(self, inter, resonite_username: str, discord_username: str = commands.Param(autocomplete=autocomp_discord_members)):
        await inter.response.defer()
        self._log_action(inter, resonite_username, 'add')
        if not resonite_username.startswith('U-'):
            await self.msg_warning(inter, "Please be sure to precise the 'U-' before the resonite username!")
            return
        elif all(x not in discord_username for x in ('@', '#')):
            await self.msg_warning(inter, "The discord username must be either a discord name + discrininator or an id starting with `@`")
            return
        guild_members = inter.guild.members
        discord_id = None
        for member in guild_members:
            if discord_username == f"{member.name}#{member.discriminator}" or discord_username.replace('@', '') == str(member.id):
                discord_id = str(member.id)
                discord_handle = f"{member.name}#{member.discriminator}"
        if not discord_id:
            await self.msg_error(
                inter,
                f"No discord id has been found for {str(member.id)}. Tip: Don't copy past the discord + username but let discord slash comand help you fill the field. For example you could have space by mistake before the `#` sign.",
            )
            return
        resonite_username = resonite_username.replace(' ', '-') # Automaticly replace all space for dash like resonite
        if not self._user_exist(resonite_username):
            try:
                self._setCloudVar(
                    resonite_username, f"{RESONITE_VAR_GROUP}.{RESONITE_VAR_PATH}", 'True'
                )
            except ValueError as exc:
                await self.msg_error(inter, exc)
                return
            self.db_session.add(
                User(
                    resonite_username,
                    discord_id,
                    inter.user.id,
                )
            )
            self.db_session.commit()
            await self.msg_working(inter, f"Adding user {resonite_username} to the accesslist...")
            if DISCORD_LOG_OUTPUT_CHANNEL:
                await self._update_channel(resonite_username, discord_handle, discord_id, inter.user.id, f"{inter.user.name}#{inter.user.discriminator}", inter.guild.id)
            else:
                am_logger.info('No output channel configured, ignoring channel log update.')
            await self.msg_success(inter, f"User {resonite_username} added to the accesslist")
        else:
            await self.msg_info(inter, f"User {resonite_username} already added to the accesslist")

    @accesslist.sub_command(
        name='remove',
        description='Removes an user from the cloud variable')
    async def remove(self, inter, username: str = commands.Param(autocomplete=autocomp_members)):
        await inter.response.defer()
        if all(x not in username for x in ('U-', '#', '@')):
            await self.msg_warning(
                inter,
                "The username must either start with U- for resonite or contains the discord hashtag number for discord one")
            return
        username_str = username
        guild_members = inter.guild.members
        if '#' in username:
            for member in guild_members:
                if f"{member.name}#{member.discriminator}" == username:
                    username_name = username
                    username = str(member.id)
            self._log_action(inter, [username_name, username], 'remove')
        elif username.startswith('@'):
            username = username.replace('@', '', 1)
            for member in guild_members:
                if username == str(member.id):
                    username_str = f"{member.name}#{member.discriminator}"
            self._log_action(inter, [username_str, username], 'remove')
        else:
            username = username.replace(' ', '-') # Automaticly replace all space for dash like resonite
            self._log_action(inter, username, 'remove')
        if not username.startswith('U-'):
            resonite_user = self.db_session.query(User).filter(User.discord_id == username)
            if resonite_user.count():
                username = resonite_user[0].resonite_username
            else:
                message = (f'User {username} already removed from the accesslist\n')
                await self.msg_info(inter, message)
                return
        try:
            self._setCloudVar(
                username, f"{RESONITE_VAR_GROUP}.{RESONITE_VAR_PATH}", 'False'
            )
        except ValueError as exc:
            await self.msg_error(inter, exc)
            return
        if self._user_exist(username):
            if username.startswith('U-'):
                resonite_user = self.db_session.query(User).filter(User.resonite_username == username)[0]
            else:
                resonite_user = self.db_session.query(User).filter(User.discord_id == username)[0]
            self.db_session.delete(resonite_user)
            self.db_session.commit()
        await self.msg_success(
            inter,
            f'User {username_str} removed from the accesslist'
        )

    @accesslist.sub_command(
        name='search',
        description='Returns if an user information')
    async def search(
            self,
            inter, username: str = commands.Param(autocomplete=autocomp_members),
            type: str = commands.Param(
                choices={"User": "user", "Verifier": "verifier"})
        ):
        await inter.response.defer()
        self._log_action(inter, username, 'search')
        if type == 'verifier':
            if all(x not in username for x in ('#', '@')):
                await self.msg_warning(
                    inter,
                    "When searching for a verifier either:\n"
                    "- Use a discord username who must contain the hashtag number\n"
                    "- Use the discord id who must start with @")
                return
            if '#' in username:
                guild_members = inter.guild.members
                for member in guild_members:
                    if f"{member.name}#{member.discriminator}" == username:
                        username = str(member.id)
            elif username.startswith('@'):
                username = username.replace('@', '', 1)
            else:
                username = username.replace(' ', '-') # Automaticly replace all space for dash like resonite
            resonite_users = self.db_session.query(User).filter(User.verifier == username)
            if resonite_users:
                users = "".join([f" - {user} (<@{user.discord_id}>)\n" for user in resonite_users])
                formated_text = (
                    f"<@{username}> had accepted the following users in the past:\n"
                    f"{users}"
                )
            else:
                formated_text = f"{username} have not yet accepted users"
            await self.msg_info(inter, formated_text)
        else:
            guild_members = inter.guild.members
            username_name = username
            if '#' in username:
                for member in guild_members:
                    if f"{member.name}#{member.discriminator}" == username:
                        username = str(member.id)
                        username_name = f"<@{username}> ({member.name}#{member.discriminator})"
            elif username.startswith('@'):
                username = username.replace('@', '', 1)
                for member in guild_members:
                    if str(member.id) == username:
                        username_name = f"<@{username}> ({member.name}#{member.discriminator})"
            else:
                username = username.replace(' ', '-') # Automaticly replace all space for dash like resonite
                username_name = username
            if self._user_exist(username):
                if username.startswith('U-'):
                    resonite_user = self.db_session.query(User).filter(User.resonite_username == username)[0]
                else:
                    resonite_user = self.db_session.query(User).filter(User.discord_id == username)[0]
                    username = resonite_user.resonite_username
                resonite_discord_username = None
                verifier_discord_username = None
                for member in guild_members:
                    if str(member.id) == resonite_user.discord_id:
                        resonite_discord_username = f"{member.name}#{member.discriminator}"
                    if str(member.id) == resonite_user.verifier:
                        verifier_discord_username = f"{member.name}#{member.discriminator}"
                resonite_discord_username = resonite_discord_username if resonite_discord_username else "<??>"
                verifier_discord_username = verifier_discord_username if verifier_discord_username else "<??>"
                cloud_var_value = self._getCloudVar(username, f"{RESONITE_VAR_GROUP}.{RESONITE_VAR_PATH}")
                formated_text = (
                    f"**Resonite U- username:** {resonite_user.resonite_username}\n"
                    f"**Discord username:** <@{resonite_user.discord_id}> ({resonite_discord_username})\n"
                    f"**Verifier discord username:** <@{resonite_user.verifier}> ({verifier_discord_username})\n"
                    f"**Verification date:** {resonite_user.verified_date} ({resonite_user.verified_date})\n"
                    f"**Cloud variable status:** {cloud_var_value}"
                )
            elif username.startswith('U-'):
                cloud_var_value = self._getCloudVar(username, f"{RESONITE_VAR_GROUP}.{RESONITE_VAR_PATH}")
                formated_text = (
                    f"**Resonite U- username:** {username}\n"
                    f"**Cloud variable status:** {cloud_var_value}"
                )
                if 'true' in cloud_var_value:
                    formated_text += '\n**WARNING**: Cloud variable set to true but user is not in the database!'
            else:
                formated_text = (
                    f"No discord user found for {username_name}.\n"
                    "Use directly the U- user to directly check the value of the cloud variable."
                )
            await self.msg_info(inter, formated_text)

    @accesslist.sub_command(name='resetlogs', description='Reset the log output channel and relog the content of the database')
    async def resetlogs(self, inter, log: bool = True):
        await inter.response.defer()
        if not DISCORD_LOG_OUTPUT_CHANNEL:
            await self.msg_warning(inter, "Cant reset! Channel not setup!")
            return
        await self.msg_working(inter, "Reset in progress... please be patient...")
        channel = disnake.utils.get(self.bot.get_all_channels(), guild__id=inter.guild.id, name=DISCORD_LOG_OUTPUT_CHANNEL)
        async for msg in channel.history(limit=1000):
            if msg.author.id == self.bot.application_id:
                await msg.delete()
                await asyncio.sleep(1.2)
        if log:
            users = self.db_session.query(User).all()
            for user in users:
                try:
                    resonite_user = self.resonite_client.getUserData(user.resonite_username)
                    resonite_username = resonite_user.username
                except Exception:
                    am_logger.error(traceback.format_exc())
                    resonite_username = "<??>"
                try:
                    discord_user = self.bot.get_user(int(user.discord_id))
                except Exception:
                    am_logger.error(traceback.format_exc())
                    discord_user = None
                if discord_user:
                    discord_handle = f"{discord_user.name}#{discord_user.discriminator}"
                else:
                    discord_handle = user.discord_id
                verifier_user = self.bot.get_user(int(user.verifier))
                if verifier_user:
                    verifier_handle = f"{verifier_user.name}#{verifier_user.discriminator}"
                else:
                    verifier_handle = user.verifier

                await channel.send(self._log_format(
                    resonite_username, user.resonite_username, discord_handle,
                    user.discord_id, user.verifier, verifier_handle)
                )
                time.sleep(1)
        await self.msg_success(inter, "Reset done!")

    def _user_exist(self, username):
        if username.startswith('U-'):
            resonite_users = self.db_session.query(User).filter(User.resonite_username == username)
        else:
            resonite_users = self.db_session.query(User).filter(User.discord_id == username)
        return bool(
            resonite_users.count()
        )

    def _log_action(self, inter, username, action):
        if isinstance(username, list):
            username = f"{username[0]}(@{username[1]})"
        usage_logger.warning(f'[{inter.guild.name}:{inter.guild.id}] [{inter.channel.name}:{inter.channel.id}] [{inter.author.display_name}:{inter.author.name}] - {action} {username}')

    def _getCloudVar(self, username, path):
        try:
            try:
                cloud_var = self.resonite_client.getCloudVar(username, path)
            except InvalidToken:
                login(self.resonite_client)
                cloud_var = self.resonite_client.getCloudVar(username, path)
            if cloud_var.timestamp == '0001-01-01T00:00:00+00:00':
                cloud_var_value = "Value never set!"
            else:
                cloud_var_value = cloud_var.value
        except ResoniteAPIException as exc:
            if exc.json['title'] == 'Not Found':
                cloud_var_value = f'{path} cloud variable doesnt exist.'
            else:
                cloud_var_value = exc
        return cloud_var_value

    def _setCloudVar(self, owner_id, path, value):
        try:
            try:
                self.resonite_client.setCloudVar(owner_id, path, value)
            except InvalidToken:
                login(self.resonite_client)
                self.resonite_client.setCloudVar(owner_id, path, value)
        except ResoniteAPIException as exc:
            if 'Invalid OwnerID' in str(exc):
                message = f"{owner_id} not found"
            else:
                am_logger.error(traceback.format_exc())
                am_logger.error(f"Trying to set cloud variable `{path}` for `{owner_id}` with `{value}`")
                message = "Error when setting the cloud variable, check the logs"
            raise ValueError(message)

    def _log_format(self, resonite_username, resonite_user_id, discord_handle, discord_id, verified_id, verified_discord_handle, guild_id=None, msg_history=None):
        line = f"User Discord: <@{discord_id}> ({discord_handle}) | User ResoniteVR: {resonite_user_id} ({resonite_username}) | Verifier Discord: <@{verified_id}> ({verified_discord_handle})"
        if msg_history:
            for msg in msg_history:
                if msg.author.id == self.bot.application_id and msg.content == line:
                    am_logger.info(f"{resonite_user_id} already logged.")
                    return ''
            return line
        else:
            return line

    async def _update_channel(self, resonite_user_id, discord_handle, discord_id, verified_id, verified_discord_handle, guild_id):
        channel = disnake.utils.get(self.bot.get_all_channels(), guild__id=guild_id, name=DISCORD_LOG_OUTPUT_CHANNEL)

        try:
            resonite_user = self.resonite_client.getUserData(resonite_user_id)
            resonite_username = resonite_user.username
        except Exception:
            am_logger.error(traceback.format_exc())
            resonite_username = "<??>"

        msg_history = await channel.history(limit=1000).flatten()

        log = self._log_format(resonite_username, resonite_user_id, discord_handle, discord_id, verified_id, verified_discord_handle, guild_id, msg_history)
        if log:
            await channel.send(log)

    async def msg_working(self, inter, message):
        await inter.followup.send(
            f':arrows_counterclockwise: {message}'
        )

    async def msg_error(self, inter, message):
        await inter.followup.send(
            f':fire: {message}'
        )

    async def msg_success(self, inter, message):
        await inter.followup.send(
            f':white_check_mark: {message}'
        )

    async def msg_warning(self, inter, message):
        await inter.followup.send(
            f':warning: {message}'
        )

    async def msg_info(self, inter, message):
        await inter.followup.send(
            f':information_source: {message}'
        )
