#!/bin/python

import sys
import logging
import sqlite3
import traceback
import time
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

import disnake
from disnake.ext import commands

from neos.client import Client
from neos.classes import LoginDetails

from config import DISCORD_BOT_TOKEN, NEOS_USERNAME, NEOS_PASSWORD

logging_format = '%(asctime)s %(levelname)s %(name)s %(message)s'
logging_datefmt = '%Y-%m-%d %H:%M:%S'
log_formatter = logging.Formatter(logging_format, logging_datefmt)

logging.basicConfig(
        level=logging.WARNING,
        format=logging_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("access_manager.log", mode='a')
        ],
        datefmt=logging_datefmt
    )

logging.Formatter.converter = time.gmtime

usage_logger = logging.getLogger('access_manager.usage')
usage_logger.setLevel(logging.INFO)

am_logger = logging.getLogger('access_manager')
am_logger.setLevel(logging.INFO)

client = Client()

client.login(
    LoginDetails(username=NEOS_USERNAME, password=NEOS_PASSWORD)
)


class User(Base):
    __tablename__ = 'neos_user'

    id = Column(Integer, primary_key=True)
    neos_username = Column(Text, unique=True, nullable=False)
    discord_id = Column(Text, nullable=False)
    verifier = Column(Text, nullable=False)
    verified_date = Column(DateTime, default=datetime.utcnow)

    def __init__(
            self, neos_username, discord_id, verifier,
            verified_date = None
    ):
        self.neos_username = neos_username
        self.discord_id = discord_id
        self.verifier = verifier
        if verified_date:
            self.verified_date = verified_date

    def __str__(self):
        return self.neos_username

    def __repr__(self):
        return self.__str__()

engine = create_engine('sqlite:///accesslist.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

def user_exist(username):
    if username.startswith('U-'):
        neos_users = session.query(User).filter(User.neos_username == username)
    else:
        neos_users = session.query(User).filter(User.discord_id == username)
    return bool(
        neos_users.count()
    )

def log_action(inter, username, action):
    if isinstance(username, list):
        username = f"{username[0]}(@{username[1]})"
    usage_logger.warning(f'[{inter.guild.name}:{inter.guild.id}] [{inter.channel.name}:{inter.channel.id}] [{inter.author.display_name}:{inter.author.name}] - {action} {username}')

def send_cmd(cmd, second=False):
    client.sendMessageLegacy('U-USFN-Orion', 'U-Neos', cmd)
    msgs = client.getMessageLegacy(maxItems=10, user='U-Neos')
    try:
        cmd_index = next((i for (i, d) in enumerate(msgs) if d["content"] == cmd), None)
        try:
            resp_index = cmd_index - 1
        except TypeError as exc:
            if not second:
                return send_cmd(cmd)
            else:
                raise exc
        return msgs[resp_index]['content']
    except (TypeError, IndexError) as exc:
        print('Command user:')
        print(cmd)
        print('Last messages from U-Neos:')
        for msg in msgs:
            print(msg['sendTime'], msg['content'])
        print(traceback.format_exc())
        raise ValueError('Something is wrong with the neos API, check the bot logs')

async def autocomp_members(inter: disnake.ApplicationCommandInteraction, user_input: str):
    if user_input.startswith('U-'):
        members = session.query(User).filter(User.neos_username.startswith(user_input)).all()
        members = [member.neos_username for member in members]
    elif len(user_input) > 1:
        members = inter.guild.members
        members = [f"{member.name}#{member.discriminator}" for member in members if member.name.startswith(user_input)]
    else:
        members = session.query(User).filter(User.neos_username.startswith(user_input)).all()
        members = [member.neos_username for member in members]
        _members = inter.guild.members
        members.extend([f"{member.name}#{member.discriminator}" for member in _members if member.name.startswith(user_input)])
    return members[:25]


class AccessList(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description='Manage USFN AD accesslist')
    async def accesslist(self, inter):
        pass

    @accesslist.sub_command(name='add', description='Adds a new users to the cloud variable')
    async def add(self, inter, neos_username: str, discord_username: str = commands.Param(autocomplete=autocomp_members)):
        log_action(inter, neos_username, 'add')
        if not neos_username.startswith('U-'):
            await inter.response.send_message("Please be sure to precise the 'U-' before the neos username!")
            return
        elif all(x not in discord_username for x in ('@', '#')):
            await inter.response.send_message("The discord username must also have the discord tag!")
            return
        guild_members = inter.guild.members
        if '#' in discord_username:
            for member in guild_members:
                if f"{member.name}#{member.discriminator}" == discord_username:
                    discord_username = str(member.id)
        elif discord_username.startswith('@'):
            discord_username = discord_username.replace('@', '')
        neos_username = neos_username.replace(' ', '-') # Automaticly replace all space for dash like neos
        if not user_exist(neos_username):
            try:
                cmd = f'/setGroupVarValue G-United-Space-Force-N orion.userAccess {neos_username} true'
                cloud_var = send_cmd(cmd)
                if cloud_var == 'Variable set!':
                    message = f'User {neos_username} added to the accesslist'
                else:
                    am_logger.error(cmd)
                    am_logger.error(cloud_var)
                    message = (
                        "Error when setting the cloud variable:\n"
                        f"{cloud_var}"
                    )
                    await inter.response.send_message(message)
                    return
            except ValueError:
                message = 'Something is wrong, check logs'
            session.add(
                User(
                    neos_username,
                    discord_username,
                    inter.user.id,
                )
            )
            session.commit()
            await inter.response.send_message(message)
        else:
            message = f'User {neos_username} already added to the accesstlist'
            await inter.response.send_message(message)

    @accesslist.sub_command(
        name='remove',
        description='Removes an user, by `U-` neos or discord username from the cloud variable')
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
            log_action(inter, [username_name, username], 'remove')
        elif username.startswith('@'):
            username = username.replace('@', '', 1)
            for member in guild_members:
                if username == str(member.id):
                    username_str = f"{member.name}#{member.discriminator}"
            log_action(inter, [username_str, username], 'remove')
        else:
            username = username.replace(' ', '-') # Automaticly replace all space for dash like neos
            log_action(inter, username, 'remove')
        if not username.startswith('U-'):
            neos_user = session.query(User).filter(User.discord_id == username)
            if neos_user.count():
                username = neos_user[0].neos_username
            else:
                message = (f'User {username_str} already removed from the accesslist\n')
                await inter.response.send_message(message)
                return
        try:
            cmd = f'/setGroupVarValue G-United-Space-Force-N orion.userAccess {username} false'
            cloud_var = send_cmd(cmd)
            if cloud_var == 'Variable set!':
                message = f'User {username} removed from the accesstlist'
            else:
                am_logger.error(cmd)
                am_logger.error(cloud_var)
                message = (
                    "Error when setting the cloud variable:\n"
                    f"{cloud_var}"
                )
                await inter.response.send_message(message)
                return
        except ValueError:
            message = 'Something is wrong, check logs'
            await inter.response.send_message(message)
            return
        if user_exist(username):
            if username.startswith('U-'):
                neos_user = session.query(User).filter(User.neos_username == username)[0]
            else:
                neos_user = session.query(User).filter(User.discord_id == username)[0]
            session.delete(neos_user)
            session.commit()
            await inter.response.send_message(message)
        else:
            message = (f'User {username_str} removed from the accesslist\n')
            await inter.response.send_message(message)

    @accesslist.sub_command(
        name='search',
        description='Returns if an user, by `U-` neos or discord username is in the cloud variable')
    async def search(
            self,
            inter, username: str = commands.Param(autocomplete=autocomp_members),
            type: str = commands.Param(
                choices={"User": "user", "Verifier": "verifier"})
        ):
        log_action(inter, username, 'search')
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
            neos_users = session.query(User).filter(User.verifier == username)
            if neos_users:
                users = "".join([f" - {user}\n" for user in neos_users])
                formated_text = (
                    f"{username} had accepted the following users in the past:\n"
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
            if user_exist(username):
                if username.startswith('U-'):
                    neos_user = session.query(User).filter(User.neos_username == username)[0]
                else:
                    neos_user = session.query(User).filter(User.discord_id == username)[0]
                    username = neos_user.neos_username
                for member in guild_members:
                    if str(member.id) == neos_user.discord_id:
                        neos_discord_username = f"{member.name}#{member.discriminator}"
                    if str(member.id) == neos_user.verifier:
                        verifier_discord_username = f"{member.name}#{member.discriminator}"
                try:
                    cmd = f'/getGroupVarValue G-United-Space-Force-N orion.userAccess {username}'
                    cloud_var = send_cmd(cmd)
                    if "Value:" not in cloud_var:
                        am_logger.error(cmd)
                        am_logger.error(cloud_var)
                        message = (
                        "Error when getting the cloud variable:\n"
                            f"{cmd}"
                        )
                        await inter.response.send_message(message)
                        return
                except ValueError as exc:
                    cloud_var = exc
                formated_text = (
                    f"**Neos U- username:** {neos_user.neos_username}\n"
                    f"**Discord username:** <@{neos_user.discord_id}> ({neos_discord_username})\n"
                    f"**Verifier discord username:** <@{neos_user.verifier}> ({verifier_discord_username})\n"
                    f"**Verification date:** {neos_user.verified_date} ({neos_user.verified_date})\n"
                    f"**Cloud variable status:** {cloud_var}"
                )
            elif username.startswith('U-'):
                try:
                    cmd = f'/getGroupVarValue G-United-Space-Force-N orion.userAccess {username}'
                    cloud_var = send_cmd(cmd)
                    if "Value:" not in cloud_var:
                        am_logger.error(cmd)
                        am_logger.error(cloud_var)
                        message = (
                        "Error when getting the cloud variable:\n"
                            f"{cmd}"
                        )
                        await inter.response.send_message(message)
                        return
                except ValueError as exc:
                    cloud_var = exc
                formated_text = (
                    f"**Neos U- username:** {username}\n"
                    f"**Cloud variable status:** {cloud_var}"
                )
                if 'true' in cloud_var:
                    formated_text += '\n**WARNING**: Cloud variable set to true but user is not in the database!'
            else:
                formated_text = (
                    f"No discord user found for {username_name}.\n"
                    "Use directly the U- user to directly check the value of the cloud variable."
                )
            await inter.response.send_message(formated_text)

am_logger.info('Starting access manager')

intents = disnake.Intents.all()
bot = commands.InteractionBot(intents=intents)

@bot.event
async def on_ready():
    am_logger.info("Access manager discord bot is ready!")

bot.add_cog(AccessList(bot))
bot.run(DISCORD_BOT_TOKEN)
