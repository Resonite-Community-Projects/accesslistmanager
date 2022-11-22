import traceback
import asyncio
import time

import disnake
from disnake.ext import commands
from neos.classes import LoginDetails
from neos.exceptions import InvalidToken, NeosAPIException

from accesslistmanager.config import NEOS_PASSWORD, NEOS_USERNAME, NEOS_VAR_GROUP, NEOS_VAR_PATH
from accesslistmanager.logger import am_logger, usage_logger
from accesslistmanager.models import Session, User
from accesslistmanager.utils import login

db_session = Session()

NEOS_VAR_GROUP = NEOS_VAR_GROUP[:22]
async def autocomp_members(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if user_input.startswith('U-'):
        members = db_session.query(User).filter(User.neos_username.startswith(user_input)).all()
        members = [member.neos_username for member in members]
    elif len(user_input) > 1:
        members = inter.guild.members
        members = [f"{member.name}#{member.discriminator}" for member in members if member.name.startswith(user_input)]
    else:
        members = db_session.query(User).filter(User.neos_username.startswith(user_input)).all()
        members = [member.neos_username for member in members]
        _members = inter.guild.members
        members.extend([f"{member.name}#{member.discriminator}" for member in _members if member.name.startswith(user_input)])
    return members[:25]

async def autocomp_discord_members(inter: disnake.ApplicationCommandInteraction, user_input: str):
    members = inter.guild.members
    members = [f"{member.name}#{member.discriminator}" for member in members if member.name.startswith(user_input)]
    return members[:25]


class AccessList(commands.Cog):

    def __init__(self, bot, db_session, neos_client):
        self.bot = bot
        self.db_session = db_session
        self.neos_client = neos_client

    @commands.slash_command(description='Manage accesslist')
    async def accesslist(self, inter):
        pass

    @accesslist.sub_command(name='add', description='Adds a new users to the cloud variable')
    async def add(self, inter, neos_username: str, discord_username: str = commands.Param(autocomplete=autocomp_discord_members)):
        self._log_action(inter, neos_username, 'add')
        if not neos_username.startswith('U-'):
            await inter.response.send_message("Please be sure to precise the 'U-' before the neos username!")
            return
        elif all(x not in discord_username for x in ('@', '#')):
            await inter.response.send_message("The discord username must be either a discord name + discrininator or an id starting with `@`")
            return
        guild_members = inter.guild.members
        for member in guild_members:
            if discord_username == f"{member.name}#{member.discriminator}" or discord_username.replace('@', '') == str(member.id):
                discord_id = str(member.id)
                discord_handle = f"{member.name}#{member.discriminator}"
        neos_username = neos_username.replace(' ', '-') # Automaticly replace all space for dash like neos
        if not self._user_exist(neos_username):
            try:
                self._setCloudVar(
                    neos_username, f"{NEOS_VAR_GROUP}.{NEOS_VAR_PATH}", True
                )
            except ValueError as exc:
                await inter.response.send_message(exc)
                return
            self.db_session.add(
                User(
                    neos_username,
                    discord_id,
                    inter.user.id,
                )
            )
            self.db_session.commit()
            await self.update_channel(neos_username, discord_handle, discord_id, inter.user.id, f"{inter.user.name}#{inter.user.discriminator}", inter.guild.id)
            await inter.response.send_message(
                f'User {neos_username} added to the accesslist'
            )
        else:
            message = f'User {neos_username} already added to the accesstlist'
            await inter.response.send_message(message)

    @accesslist.sub_command(
        name='remove',
        description='Removes an user from the cloud variable')
    async def remove(self, inter, username: str = commands.Param(autocomplete=autocomp_members)):
        if all(x not in username for x in ('U-', '#', '@')):
            await inter.response.send_message(
                "The username must either start with U- for neos or contains the discord hashtag number for discord one")
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
            username = username.replace(' ', '-') # Automaticly replace all space for dash like neos
            self._log_action(inter, username, 'remove')
        if not username.startswith('U-'):
            neos_user = self.db_session.query(User).filter(User.discord_id == username)
            if neos_user.count():
                username = neos_user[0].neos_username
            else:
                message = (f'User {username_str} already removed from the accesslist\n')
                await inter.response.send_message(message)
                return
        try:
            self._setCloudVar(
                username_str, f"{NEOS_VAR_GROUP}.{NEOS_VAR_PATH}", False
            )
        except ValueError as exc:
            await inter.response.send_message(exc)
            return
        if self._user_exist(username):
            if username.startswith('U-'):
                neos_user = self.db_session.query(User).filter(User.neos_username == username)[0]
            else:
                neos_user = self.db_session.query(User).filter(User.discord_id == username)[0]
            self.db_session.delete(neos_user)
            self.db_session.commit()
            await inter.response.send_message(
                f'User {username_str} removed to the accesslist'
            )
        else:
            await inter.response.send_message(
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
        self._log_action(inter, username, 'search')
        if type == 'verifier':
            if all(x not in username for x in ('#', '@')):
                await inter.response.send_message(
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
                username = username.replace(' ', '-') # Automaticly replace all space for dash like neos
            neos_users = self.db_session.query(User).filter(User.verifier == username)
            if neos_users:
                users = "".join([f" - {user} (<@{user.discord_id}>)\n" for user in neos_users])
                formated_text = (
                    f"<@{username}> had accepted the following users in the past:\n"
                    f"{users}"
                )
            else:
                formated_text = f"{username} have not yet accepted users"
            await inter.response.send_message(formated_text)
        else:
            guild_members = inter.guild.members
            if '#' in username:
                for member in guild_members:
                    if f"{member.name}#{member.discriminator}" == username:
                        username_name = username
                        username = str(member.id)
            elif username.startswith('@'):
                username = username.replace('@', '', 1)
                for member in guild_members:
                    if str(member.id) == username:
                        username_name = f"<@{username}> ({member.name}#{member.discriminator})"
            else:
                username = username.replace(' ', '-') # Automaticly replace all space for dash like neos
                username_name = username
            if self._user_exist(username):
                if username.startswith('U-'):
                    neos_user = self.db_session.query(User).filter(User.neos_username == username)[0]
                else:
                    neos_user = self.db_session.query(User).filter(User.discord_id == username)[0]
                    username = neos_user.neos_username
                for member in guild_members:
                    if str(member.id) == neos_user.discord_id:
                        neos_discord_username = f"{member.name}#{member.discriminator}"
                    if str(member.id) == neos_user.verifier:
                        verifier_discord_username = f"{member.name}#{member.discriminator}"
                cloud_var_value = self._getCloudVar(username, f"{NEOS_VAR_GROUP}.{NEOS_VAR_PATH}")
                formated_text = (
                    f"**Neos U- username:** {neos_user.neos_username}\n"
                    f"**Discord username:** <@{neos_user.discord_id}> ({neos_discord_username})\n"
                    f"**Verifier discord username:** <@{neos_user.verifier}> ({verifier_discord_username})\n"
                    f"**Verification date:** {neos_user.verified_date} ({neos_user.verified_date})\n"
                    f"**Cloud variable status:** {cloud_var_value}"
                )
            elif username.startswith('U-'):
                cloud_var_value = self._getCloudVar(username, f"{NEOS_VAR_GROUP}.{NEOS_VAR_PATH}")
                formated_text = (
                    f"**Neos U- username:** {username}\n"
                    f"**Cloud variable status:** {cloud_var_value}"
                )
                if 'true' in cloud_var_value:
                    formated_text += '\n**WARNING**: Cloud variable set to true but user is not in the database!'
            else:
                formated_text = (
                    f"No discord user found for {username}.\n"
                    "Use directly the U- user to directly check the value of the cloud variable."
                )
            await inter.response.send_message(formated_text)

    def _user_exist(self, username):
        if username.startswith('U-'):
            neos_users = self.db_session.query(User).filter(User.neos_username == username)
        else:
            neos_users = self.db_session.query(User).filter(User.discord_id == username)
        return bool(
            neos_users.count()
        )

    def _log_action(self, inter, username, action):
        if isinstance(username, list):
            username = f"{username[0]}(@{username[1]})"
        usage_logger.warning(f'[{inter.guild.name}:{inter.guild.id}] [{inter.channel.name}:{inter.channel.id}] [{inter.author.display_name}:{inter.author.name}] - {action} {username}')

    def _getCloudVar(self, username, path):
        try:
            try:
                cloud_var = self.neos_client.getCloudVar(username, path)
            except InvalidToken:
                login(self.neos_client)
                cloud_var = self.neos_client.getCloudVar(username, path)
            if cloud_var['timestamp'] == '0001-01-01T00:00:00+00:00':
                cloud_var_value = "Value never set!"
            else:
                cloud_var_value = cloud_var['value']
        except NeosAPIException as exc:
            if exc.json['title'] == 'Not Found':
                cloud_var_value = f'{path} cloud variable doesnt exist.'
            else:
                cloud_var_value = exc
        return cloud_var_value

    def _setCloudVar(self, username, path, value):
        try:
            try:
                self.neos_client.setCloudVar(username, path, value)
            except InvalidToken:
                login(self.neos_client)
                self.neos_client.setCloudVar(username, path, value)
        except NeosAPIException as exc:
            if 'Invalid OwnerID' in str(exc):
                message = f"{username} not found"
            else:
                am_logger.error(traceback.format_exc())
                am_logger.error(f"Trying to set cloud variable `{path}` for `{username}` with `{value}`")
                message = "Error when setting the cloud variable, check the logs"
            raise ValueError(message)

    #@accesslist.sub_command(name='test', description='test Adds a new users to the cloud variable')
    #async def test(self, inter, neos_username: str, discord_username: str = commands.Param(autocomplete=autocomp_discord_members)):
    #    await self.update_channel(neos_username, discord_username, inter.user.id, inter.guild.id)

    @accesslist.sub_command(name='resetlogs', description='Reset the log output channel and relog the content of the database')
    async def resetlogs(self, inter):
        await inter.response.send_message("Reset in progress... please be patient...")
        await self.reset_channel(inter.guild.id)

    def log_format(self, neos_username, neos_user_id, discord_handle, discord_id, verified_id, verified_discord_handle):
        return f"User Discord: <@{discord_id}> ({discord_handle}) | User NeosVR: {neos_user_id} ({neos_username}) | Verifier Discord: <@{verified_id}> ({verified_discord_handle})"

    async def reset_channel(self, guild_id):
        channel = disnake.utils.get(self.bot.get_all_channels(), guild__id=guild_id, name="output")
        async for msg in channel.history(limit=1000):
            if msg.author.id == self.bot.application_id:
                await msg.delete()
                await asyncio.sleep(1.2)
        users = self.db_session.query(User).all()
        _users = []
        for x in range(600):
            _users.append(users[0])
        users = _users
        for user in users:
            try:
                neos_user = self.neos_client.getUserData(user.neos_username)
                neos_username = neos_user.username
            except Exception as exc:
                am_logger.error(traceback.format_exc())
                neos_username = "<??>"
            discord_user = self.bot.get_user(int(user.discord_id))
            verifier_user = self.bot.get_user(int(user.verifier))
            channel = disnake.utils.get(self.bot.get_all_channels(), guild__id=guild_id, name="output")
            await channel.send(self.log_format(
                neos_username, user.neos_username, f"{discord_user.name}#{discord_user.discriminator}",
                user.discord_id, user.verifier, f"{verifier_user.name}#{verifier_user.discriminator}")
            )
            time.sleep(1)
        print("Clean done")

    async def update_channel(self, neos_user_id, discord_handle, discord_id, verified_id, verified_discord_handle, guild_id):
        channel = disnake.utils.get(self.bot.get_all_channels(), guild__id=guild_id, name="output")

        try:
            neos_user = self.neos_client.getUserData(neos_user_id)
            neos_username = neos_user.username
        except Exception as exc:
            am_logger.error(traceback.format_exc())
            neos_username = "<??>"

        await channel.send(self.log_format(neos_username, neos_user_id, discord_handle, discord_id, verified_id, verified_discord_handle))