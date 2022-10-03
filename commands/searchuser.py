from disnake.ext import commands

from neos.exceptions import InvalidToken

class SearchUser(commands.Cog):

    def __init__(self, bot, db_session, neos_client):
        self.bot = bot
        self.db_session = db_session
        self.neos_client = neos_client

    @commands.slash_command(description='Search a NeosVR user per username')
    async def searchuser(self, inter, username: str):
        try:
            users = self.neos_client.searchUser(username)
        except InvalidToken:
            login()
            users = self.neos_client.searchUser(username)
        if users:
            users = "".join([f" - {user['id']} ({user['username']})\n" for user in users])
            formated_text = (
                f"Here is the following users corresponding to the search `{username}`:\n"
                f"{users}"
            )
        else:
            formated_text = f'Nothing found for the search `{username}`.'
            if username.startswith('U-'):
                formated_text += (
                    " The username researched start with `U-`,"
                    " this looks like a NeosVR User Id and not a NeosVR Username."
                )
        await inter.response.send_message(formated_text)