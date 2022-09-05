#!/bin/python

import logging

from disnake.ext import commands

from config import DISCORD_BOT_TOKEN

bot = commands.InteractionBot()

logging.basicConfig(filename='discord_bot.log', level=logging.DEBUG, format='%(levelname)s %(asctime)s %(message)s')

logger = logging.getLogger('discord')
handler = logging.FileHandler(filename='discord_usage.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
logger.addHandler(handler)

def log_action(inter, username, action, status):
        logger.warning(f'[{inter.guild.name}:{inter.guild.id}] [{inter.channel.name}:{inter.channel.id}] [{inter.author.display_name}:{inter.author.name}] - {action} {username} ({status})')

@bot.slash_command(description='Manage USFN AD accesslist')
async def accesslist(inter):
    pass

@accesslist.sub_command(name='add', description='Adds a new users to the cloud variable')
async def add(inter, username: str):
    log_action(inter, username, 'add', 'success')
    await inter.response.send_message(f'/setGroupVarValue G-United-Space-Force-N orion.userAccess.bool {username} true')

@accesslist.sub_command(name='remove', description='Removes an user from the cloud variable')
async def remove(inter, username: str):
    log_action(inter, username, 'remove', 'success')
    await inter.response.send_message(f'/setGroupVarValue G-United-Space-Force-N orion.userAccess.bool {username} false')

@accesslist.sub_command(name='search', description='Returns if an user is in the cloud variable')
async def search(inter, username: str):
    log_action(inter, username, 'search', 'success')
    await inter.response.send_message(f'/getGroupVarValue G-United-Space-Force-N orion.userAccess.bool {username}')

bot.run(DISCORD_BOT_TOKEN)
