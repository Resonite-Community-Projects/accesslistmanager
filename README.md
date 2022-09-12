# AccessList Manager

## Installation

**Note:** Because of the discord bot library, disnake, the minimale version
of this project is: 3.8

```
pip install -r requirements.txt
```

## Configuration

Fill in the `config.py` file the following information:
- `NEOS_USERNAME`: neos username
- `NEOS_PASSWORD`: neos password
- `TOKEN`: discord bot token

## Usage

```
python main.py
```

## scripts

The scripts `set_from_backup.py` is used for migrate user list from an account
to the cloud variable `orion.userAccess`.

## docker-compose usage

If you want to use the docker-compose.yml you **must** first create **manually**
the files: `access_manager.log` and `accesslist.db`
