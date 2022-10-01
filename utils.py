from neos.classes import LoginDetails

from config import (
    NEOS_USERNAME, NEOS_PASSWORD,
)

def login(client):
    if client.token:
        client.clean_session()
    client.login(
        LoginDetails(ownerId=NEOS_USERNAME, password=NEOS_PASSWORD)
    )