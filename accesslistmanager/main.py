#!/bin/python

import inspect
import sqlite3
import sys
import time
import traceback
from datetime import datetime

import disnake
from neosvrpy.client import Client
from neosvrpy.exceptions import InvalidToken, NeosAPIException

from accesslistmanager.config import DISCORD_BOT_TOKEN
from accesslistmanager.logger import am_logger, usage_logger
from accesslistmanager.models import Base, Session, engine
from accesslistmanager.utils import login
from accesslistmanager import commands

neos_client = Client()
db_session = Session()

login(neos_client)

Base.metadata.create_all(engine)

am_logger.info('Starting access manager')

intents = disnake.Intents.all()
bot = disnake.ext.commands.InteractionBot(intents=intents)

@bot.event
async def on_ready():
    am_logger.info("Access manager discord bot is ready!")

for name, obj in inspect.getmembers(commands):
    if inspect.isclass(obj):
        bot.add_cog(obj(bot, db_session, neos_client))

def main():
    bot.run(DISCORD_BOT_TOKEN)
