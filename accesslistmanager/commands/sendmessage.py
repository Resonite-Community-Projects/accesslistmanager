import os
import logging
from pathlib import Path

import disnake
from disnake.ext import commands

root_dir = Path(os.path.abspath(os.curdir))
template_folder = root_dir / Path('sendmessage_templates')

def get_templates():
    if os.path.isdir(template_folder):
        return os.listdir(template_folder)
    logging.error('Error when generating the list of templates available')
    logging.error(f"Check that the folder {template_folder} exist and it's not empty")
    return []

def autocomp_templates(inter: disnake.ApplicationCommandInteraction, user_input: str):
    return get_templates()

async def autocomp_discord_members(inter: disnake.ApplicationCommandInteraction, user_input: str):
    members = inter.guild.members
    members = [f"{member.name}#{member.discriminator}" for member in members if member.name.startswith(user_input)]
    return members[:25]

class SendMessage(commands.Cog):

    def __init__(self, bot, db_session, neos_client):
        self.bot = bot
        self.db_session = db_session
        self.neos_client = neos_client

    @commands.slash_command(name="smsg", description='Send a message to a Discord User')
    async def send_message(
        self, inter,
        username: disnake.Member = commands.Param(autocomplete=autocomp_discord_members),
        template: str = commands.Param(autocomplete=autocomp_templates)
    ):
        if template in get_templates():
            with open(template_folder / template) as template_file:
                user = await username.send(template_file.read())
            formated_text = (
                f"The message based on the template `{template}` "
                f"as been send succefully to the user {username} (<@{username.id}>)"
            )
        else:
            formated_text = (
                f"`{template}` is not a valid template.\n"
                f"No message send to {username} (<@{username.id}>)"
            )
        await inter.response.send_message(formated_text)