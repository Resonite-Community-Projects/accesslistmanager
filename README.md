# Resonite Sessions CloudVariable AccessList Manager

Discord bot for managing Resonite sessions access via cloud variable.
While its mainly developed for controlling a cloud variable for control a cloud variable
it could be also used in other usage too.

## Installation


```
pip install .
```

### Configuration

Fill in the `config.py` file the following information:
- `RESONITE_USERNAME`: Resonite `U-` ID
- `RESONITE_PASSWORD`: Resonite password
- `RESONITE_VAR_GROUP`: Resonite cloud variable group owner
- `RESONITE_VAR_PATH`: Resonite cloud variable path/name
- `DISCORD_BOT_TOKEN`: Discord bot token
- `DISCORD_LOG_OUTPUT_CHANNEL`: The Discord channel where to output the logged users

### Usage

```
accesslistmanager
```

#### docker-compose usage

If you want to use the docker-compose.yml you **must** first create **manually**
the files: `access_manager.log` and `accesslist.db`.

## scripts

The scripts `set_from_backup.py` is used for migrate user list from an account
to the cloud variable `orion.userAccess`.

## Discord Usage

When the bot is registered two slash commands become available. `accesslist` is the main command and is used to manage the Resonite contact of the cloud variable. `usersearch` is a utility command that can be used to search for Resonite Username in the objectif to use the Resonite User Id for using afterward in the `accesslist` command. You can also send messages to users based on a template.

### accesslist slash command

This `accesslist` slash command give the possibility to manage a cloud variable to control access.
Here is the sub commands available:

- **add** This sub command give you the possibility to add a user to the cloud variable. Two parameters are available and mandatory, `resonite_username` and `discord_username`. The `discord_username` parameter will give you a hint and return all the discord tag of the user available in the discord server. You can also "force" a Discord User Id with `@` following of the ID. In the end the Discord User Id will be saved in the database. Each time a user is added the bot will write in the record channel on Discord.

- **remove** This sub command give you the possibility to  remove an user of the cloud variable. The parameter `username` support either a Resonite User Id, a Discord User Id or a Discord Username following by his discriminator .  There is an hint who will give you a list of all the discord tag of user available either on discord or in the database (as `U-` in the last case). Only Resonite User Id, `U-`, you will be able to remove it from the cloud variable while the user is not present in the bot database.

- **search** This sub command give you the possibility to search for an user information. Two parameters are available and mandatory, `username` and `type`. 
  The first one support either a Resonite User Id, a Discord User Id or a Discord Username following by his discriminator .  There is an hint who will give you a list of all the discord tag of user available either on discord or in the database (as `U-` in the last case).  Only Resonite User Id, `U-`, you will be able to remove it from the cloud variable while the user is not present in the bot database.
  The second one have tow possible value `User` or `Verifier` the first one will give your the information about the user while the second will give you the information about which user have been verified by the researched verifier.

- **resetlogs**: This sub command give you the ability to reset the log channel. By default it will delete everthing written by the bot then rewrite everything he have in the database. There is an option `log` who is default to `True` for write the content of the database in the channel but it can be set to `False` for just empty every messages by the bot.

**NOTE:** An username can start in 2 differents way **or** having an `#` in the middle of it:
- Starting with an **U-** as a Resonite User Id
- Starting with an **@** as a Discord User Id
- Containing a **#** in the middle as a Discord Username following by his discriminator (or tag)
- The commands **add** and **resetlogs** WILL notif every verifier on the record channel. Its a good thing to tell them to mute the channel.

### usersearch slash command

This `usersearch` slash command give the possibility to lookup an Resonite User Id via providing a Resonite Username as a parameter.

### smsg slash command

This `smsg` slash command give the possibility to send a message from a template. For the moment templates can be only modified on a folder next to the bot. By default it's named `sendmessage_templates`

## Modularity

You can add your own discord command as a module in the `commands` folder. You need to
at least create one Disnake Cog class and add it in the `__init__.py` file of the `commands` folder.
By default the database sqlalchemy session and the resonite client are passed as the second
and third parameter. Check the class `commands.searchuser.SearchUser` as an example.

## Database migration

When creating a new database migration the following command should be used: `alembic revision --autogenerate -m "message"`.

When updating the database to the last version the following command should be used `alembic upgrade head`.

**Note**: The migration should be automatic.