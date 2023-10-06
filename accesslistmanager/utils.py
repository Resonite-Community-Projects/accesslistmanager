from alembic.config import Config
from alembic import command

from resonitepy.classes import LoginDetails, LoginDetailsAuth

from accesslistmanager.config import (
    RESONITE_USERNAME, RESONITE_PASSWORD,
)

def login(client):
    if client.token:
        client.clean_session()

    client.login(
        LoginDetails(
            ownerId=RESONITE_USERNAME,
            authentication=LoginDetailsAuth(password=RESONITE_PASSWORD)
        )
    )

def run_migrations(script_location, dsn):
    alembic_cfg = Config()
    alembic_cfg.set_main_option('script_location', script_location)
    alembic_cfg.set_main_option('sqlalchemy.url', dsn)
    command.upgrade(alembic_cfg, 'head')