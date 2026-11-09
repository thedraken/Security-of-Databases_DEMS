import base64
import os
from pathlib import Path
from urllib.parse import urlsplit

import requests
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(ROOT_DIR / ".env")

USERNAME = os.getenv("HUGEGRAPH_USERNAME")
ADMIN_PASSWORD = os.getenv("HUGEGRAPH_ADMIN_PASSWORD")
BASE_URL = os.getenv("BASE_URL")
GRAPHSPACE = "DEFAULT"

# API endpoints
AUTH = f"/graphspaces/{GRAPHSPACE}/auth"
GRAPH_URL = f"{BASE_URL}/graphspaces/DEFAULT/graphs/hugegraph"

# This is used to specify the server we apply to
# has form localhost:8080
TARGET_URL = urlsplit(BASE_URL).netloc

# Authentication
auth = base64.b64encode(
    f"{USERNAME}:{ADMIN_PASSWORD}".encode()
).decode()


if not BASE_URL:
    raise RuntimeError("Set the BASE_URL environment variable.")

if not USERNAME:
    raise RuntimeError("Set the HUGEGRAPH_USERNAME environment variable.")

if not ADMIN_PASSWORD:
    raise RuntimeError("Set the HUGEGRAPH_ADMIN_PASSWORD environment variable.")

if not TARGET_URL:
    raise RuntimeError("BASE_URL must contain a valid host and port.")

def request(url:str, method, endpoint, body=None):
    """
        - Send an authenticated request and check for errors.
        - inputs:
            - method: Request Type (GET, POST, ...)
            - endpoint: url endpoint (vertexlabels, ...)
            - body: JSON body that is being sent
        - output:
            - response in JSON form or None
    """
    response = requests.request(
        method,
        f"{url}{endpoint}",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/json"
        },
        json=body,
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"{method} {endpoint}: "
            f"HTTP {response.status_code}\n"
            f"{response.text}"
        )

    data = response.json() if response.text else None

    if not response.ok:
        raise RuntimeError(
            f"{method} {endpoint} -> HTTP {response.status_code}\n"
            f"{data}"
        )

    return data