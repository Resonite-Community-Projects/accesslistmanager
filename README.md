# NeosVR Sessions CloudVariable AccessList Manager

Discord bot for managing NeosVR sessions access via cloud variable.
While its mainly developed for controlling a cloud variable for control a cloud variable
it could be also used in other usage too.

## Installation


```
pip install .
```

### Configuration

Fill in the `config.py` file the following information:
- `NEOS_USERNAME`: NeosVR `U-` ID
- `NEOS_PASSWORD`: NeosVR password
- `NEOS_VAR_GROUP`: NeosVR cloud variable group owner
- `NEOS_VAR_PATH`: NeosVR cloud variable path/name
- `DISCORD_BOT_TOKEN`: Discord bot token

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

When the bot is registered two slash commands become available. `accesslist` is the main command and is used to manage the NeosVR contact of the cloud variable. `usersearch` is a utility command that can be used to search for NeosVR Username in the objectif to use the NeosVR User Id for using afterward in the `accesslist` command.

### accesslist slash command

This `accesslist` slash command give the possibility to manage a cloud variable to control access.
There is 3 sub commands available:

- **add** This sub command give you the possibility to add a user to the cloud variable. Two parameters are available and mandatory, `neos_username` and `discord_username`. The `discord_username` parameter will give you a hint and return all the discord tag of the user available in the discord server. You can also "force" a Discord User Id with `@` following of the ID. In the end the Discord User Id will be saved in the database.

- **remove** This sub command give you the possibility to  remove an user of the cloud variable. The parameter `username` support either a NeosVR User Id, a Discord User Id or a Discord Username following by his discriminator .  There is an hint who will give you a list of all the discord tag of user available either on discord or in the database (as `U-` in the last case). Only NeosVR User Id, `U-`, you will be able to remove it from the cloud variable while the user is not present in the bot database.

- **search** This sub command give you the possibility to search for an user information. Two parameters are available and mandatory, `username` and `type`. 
  The first one support either a NeosVR User Id, a Discord User Id or a Discord Username following by his discriminator .  There is an hint who will give you a list of all the discord tag of user available either on discord or in the database (as `U-` in the last case).  Only NeosVR User Id, `U-`, you will be able to remove it from the cloud variable while the user is not present in the bot database.
  The second one have tow possible value `User` or `Verifier` the first one will give your the information about the user while the second will give you the information about which user have been verified by the researched verifier.

**NOTE:** An username can start in 2 differents way **or** having an `#` in the middle of it:
- Starting with an **U-** as a NeosVR User Id
- Starting with an **@** as a Discord User Id
- Containing a **#** in the middle as a Discord Username following by his discriminator (or tag)

### usersearch slash command

This `usersearch` slash command give the possibility to lookup an NeosVR User Id via providing a NeosVR Username as a parameter.

## Modularity

You can add your own discord command as a module in the `commands` folder. You need to
at least create one Disnake Cog class and add it in the `__init__.py` file of the `commands` folder.
By default the database sqlalchemy session and the neos client are passed as the second
and third parameter. Check the class `commands.searchuser.SearchUser` as an example.