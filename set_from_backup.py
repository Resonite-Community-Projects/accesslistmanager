import time
import signal
import sys
import json
from pathlib import Path
from neos.client import Client
from neos.classes import LoginDetails

from config import NEOS_USERNAME, NEOS_PASSWORD

client = Client()

client.login(
    LoginDetails(username=NEOS_USERNAME, password=NEOS_PASSWORD)
)

contacts_json = Path("contacts.json")

def read_contacts():
    with open(contacts_json) as f:
        return json.load(f)

def write_contacts(friends_list):
    with open(contacts_json, 'w') as f:
        json.dump(friends_list, f)

if contacts_json.is_file():
    friends_list = read_contacts()
else:
    friends_list = {}

friends = client.getFriends()
for friend in friends:
    if not friend.id in friends_list:
        friends_list[friend.id] = False

write_contacts(friends_list)

def signal_handler(sig, frame):
    write_contacts(friends_list)
    print('You pressed Ctrl+C!')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

total = len(friends_list) - 1
for (pos, (friend, updated)) in enumerate(friends_list.items()):
    if friend == 'U-Neos':
        continue
    if not updated:
        print(f"Set contact {friend} [{pos}/{total}]")
        msg = f'/setGroupVarValue G-United-Space-Force-N orion.userAccess "{friend}" true'
        try:
            client.sendMessageLegacy('U-USFN-Orion', 'U-Neos', msg)
        except Exception as exc:
            write_contacts(friends_list)
            raise exc
        friends_list[friend] = True
    else:
        print(f"Ignore already updated contact {friend} [{pos}/{total}]")
    time.sleep(60)

write_contacts(friends_list)
