"""
Usage:
    python scripts/pii.py init-key   #add a key to .env if it has none -
    Needed for encryption
    python scripts/pii.py show       #list people with their decrypted PII

    #TODO add salt and hash function, so we can test that function in graph DB
"""
import os
import sys

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

ROOT_ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
KEY_NAME = "PII_ENCRYPTION_KEY"


def _fernet():
    load_dotenv(ROOT_ENV)
    key = os.getenv(KEY_NAME)
    if not key:
        raise RuntimeError(f"{KEY_NAME} is missing from .env; "
                           "run: .venv/bin/python scripts/pii.py init-key")
    return Fernet(key.encode())


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except InvalidToken:
        raise RuntimeError("PII value could not be decrypted (wrong key or tampered data)")


def init_key():
    """Append a new key to .env except if one is already present."""
    if not os.path.exists(ROOT_ENV):
        raise RuntimeError(".env does not exist yet; create it first")
    with open(ROOT_ENV, encoding="utf-8") as file:
        content = file.read()
    if any(line.startswith(f"{KEY_NAME}=") for line in content.splitlines()):
        print(f"{KEY_NAME} already present in .env; keeping it")
        return
    if content and not content.endswith("\n"):
        content += "\n"
    with open(ROOT_ENV, "w", encoding="utf-8") as file:
        file.write(content + f"{KEY_NAME}='{Fernet.generate_key().decode()}'\n")
    os.chmod(ROOT_ENV, 0o600)
    print(f"Added {KEY_NAME} to .env")


def show():
    import common

    people = common.request(common.GRAPH_URL, "GET",
                            "/graph/vertices?label=person&limit=100000")["vertices"]
    for person in sorted(people, key=lambda p: p["properties"].get("name", "")):
        token = person["properties"].get("pii")
        print(f"{person['properties'].get('name', '?'):<35} "
              f"{decrypt(token) if token else '-'}")


if __name__ == "__main__":
    commands = {"init-key": init_key, "show": show}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print(__doc__)
        raise SystemExit(2)
    try:
        commands[sys.argv[1]]()
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
