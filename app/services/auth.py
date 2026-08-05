import os
import time
import webbrowser

import requests
from dotenv import load_dotenv

from app.services.storage import save_token
from app.services.storage import clear_token


load_dotenv()

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")

DEVICE_CODE_URL = "https://github.com/login/device/code"
TOKEN_URL = "https://github.com/login/oauth/access_token"


if not CLIENT_ID:
    raise RuntimeError(
        "Missing GITHUB_CLIENT_ID in .env"
    )


def login():
    device = request_device_code()

    print("Opening GitHub authentication...")
    
    webbrowser.open(
        device.get(
            "verification_uri_complete",
            device["verification_uri"]
        )
    )

    print(
        f"If required, enter code: {device['user_code']}"
    )

    token = poll_for_token(device)

    save_token(token)

    print("Successfully logged into GitHub!")


def request_device_code():
    response = requests.post(
        DEVICE_CODE_URL,
        headers={
            "Accept": "application/json"
        },
        data={
            "client_id": CLIENT_ID,
            "scope": "read:user repo"
        },
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def poll_for_token(device):
    interval = device.get(
        "interval",
        5
    )

    while True:
        response = requests.post(
            TOKEN_URL,
            headers={
                "Accept": "application/json"
            },
            data={
                "client_id": CLIENT_ID,
                "device_code": device["device_code"],
                "grant_type": (
                    "urn:ietf:params:oauth:grant-type:device_code"
                )
            },
            timeout=10
        )

        data = response.json()

        if "access_token" in data:
            return data["access_token"]

        if data.get("error") != "authorization_pending":
            raise RuntimeError(data)

        time.sleep(interval)

def logout():
    clear_token()

    print("Successfully logged out of GitHub!")