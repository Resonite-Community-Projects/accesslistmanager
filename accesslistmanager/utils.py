from neosvrpy.classes import LoginDetails

from accesslistmanager.config import (
    NEOS_USERNAME, NEOS_PASSWORD,
)

def login(client):
    if client.token:
        client.clean_session()
    client.login(
        LoginDetails(ownerId=NEOS_USERNAME, password=NEOS_PASSWORD)
    )