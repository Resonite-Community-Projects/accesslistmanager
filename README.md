# AccessList Manager

## Installation

## Requirements

**Note:** Because of the discord bot library, disnake, the minimale version
of this project is: 3.8

```
pip install -r requirements.txt
```

### Configuration

Fill in the `config.py` file the following information:
- `NEOS_USERNAME`: neos username
- `NEOS_PASSWORD`: neos password
- `TOKEN`: discord bot token

### Usage

```
python main.py
```

#### docker-compose usage

If you want to use the docker-compose.yml you **must** first create **manually**
the files: `access_manager.log` and `accesslist.db`

## scripts

The scripts `set_from_backup.py` is used for migrate user list from an account
to the cloud variable `orion.userAccess`.

## Discord Usage

The bot should be registered under the slash command `accesslist` and have the 3 following sub commands:

- **add** This sub command give you the possibility to add a user to the cloud variable. Two parameters are available and mandatory, `neos_username` and `discord_username`. The `discord_username` parameter will give you a hint and return all the discord tag of the user available in the discord server. You can also "force" a Discord User Id with `@` following of the ID. In the end the Discord User Id will be saved in the database.

- **remove** This sub command give you the possibility to  remove an user of the cloud variable. The parameter `username` support either a NeosVR User Id, a Discord User Id or a Discord Username following by his discriminator .  There is an hint who will give you a list of all the discord tag of user available either on discord or in the database (as `U-` in the last case). Only NeosVR User Id, `U-`, you will be able to remove it from the cloud variable while the user is not present in the bot database.

- **search** This sub command give you the possibility to search for an user information. Two parameters are available and mandatory, `username` and `type`. 
The first one support either a NeosVR User Id, a Discord User Id or a Discord Username following by his discriminator .  There is an hint who will give you a list of all the discord tag of user available either on discord or in the database (as `U-` in the last case).  Only NeosVR User Id, `U-`, you will be able to remove it from the cloud variable while the user is not present in the bot database.
The second one have tow possible value `User` or `Verifier` the first one will give your the information about the user while the second will give you the information about which user have been verified by the researched verifier.

**NOTE:** An username can start in 2 differents way **or** having an `#` in the middle of it:
- Starting with an **U-** as a NeosVR User Id
- Starting with an **@** as a Discord User Id
- Containing a **#** in the middle as a Discord Username following by his discriminator (or tag)
