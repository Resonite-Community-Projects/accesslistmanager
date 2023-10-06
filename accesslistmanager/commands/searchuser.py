from disnake.ext import commands

from resonitepy.exceptions import InvalidToken

from accesslistmanager.utils import login

class SearchUser(commands.Cog):

    def __init__(self, bot, db_session, resonite_client):
        self.bot = bot
        self.db_session = db_session
        self.resonite_client = resonite_client

    @commands.slash_command(description='Search a Resonite user per username')
    async def searchuser(self, inter, username: str):
        try:
            users = self.resonite_client.searchUser(username)
        except InvalidToken:
            login(self.resonite_client)
            users = self.resonite_client.searchUser(username)
        if users:
            users = "".join([f" - {user.id} ({user.username})\n" for user in users])
            formated_text = (
                f"Here is the following users corresponding to the search `{username}`:\n"
                f"{users}"
            )
        else:
            formated_text = f'Nothing found for the search `{username}`.'
            if username.startswith('U-'):
                formated_text += (
                    " The username researched start with `U-`,"
                    " this looks like a Resonite User Id and not a Resonite Username."
                    " Try again without the `U-` in front of this username."
                )
        await inter.response.send_message(formated_text)