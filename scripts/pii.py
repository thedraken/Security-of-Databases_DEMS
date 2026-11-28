"""
Usage:
    python scripts/pii.py init-key   #add a key to .env if it has none -
    Needed for encryption
    python scripts/pii.py show       #list people with their decrypted PII

    #TODO add salt and hash function, so we can test that function in graph DB
"""
import os
import sys
import base64
import getpass
import hashlib
import hmac
import secrets

from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

#Encryption properties
ROOT_ENV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
KEY_NAME = "PII_ENCRYPTION_KEY"

#Salt and hash properties
#How difficult the hash should be, the larger the number, the longer brute
# forcing takes
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1
#How big our salt value is
SALT_BYTES = 16

#Hash functions
def hash_secret(value: str) -> str:
    """Hash a value, this cannot be 'decrypted', but can be verified with a
    hash check instead"""
    # Generate the salt
    salt = secrets.token_bytes(SALT_BYTES)

    #hash our value using scrypt which is deliberately slow and uses a lot
    # of memory, which makes brute-forcing expensive
    digest = hashlib.scrypt(value.encode("utf-8"), salt=salt,
                            n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return "$".join(["scrypt", str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P),
                     base64.b64encode(salt).decode("ascii"),
                     base64.b64encode(digest).decode("ascii")])

def verify_secret(value: str, stored: str) -> bool:
    """Re-hash value with the stored salt/parameters and compare to the
    stored value"""
    try:
        algorithm, n, r, p, salt_b64, digest_b64 = stored.split("$")
        salt, expected = base64.b64decode(salt_b64), base64.b64decode(digest_b64)
    except ValueError:
        return False
    if algorithm != "scrypt":
        return False
    digest = hashlib.scrypt(value.encode("utf-8"), salt=salt,
                            n=int(n), r=int(r), p=int(p), dklen=len(expected))
    #If we compare with ==, the hash check will stop at the first wrong
    # byte, which leaks the info to the attackers
    return hmac.compare_digest(digest, expected)

def verify(name: str, word: str | None = None) -> bool:
    import common

    people = common.request(common.GRAPH_URL, "GET",
                            "/graph/vertices?label=person&limit=100000")["vertices"]
    person = next((p for p in people if p["properties"].get("name") == name), None)
    if person is None:
        raise RuntimeError(f"No person named {name!r}")
    stored = person["properties"].get("safe_word")
    if not stored:
        raise RuntimeError(f"{name!r} has no safe word")
    if word is None:
        word = getpass.getpass("Safe word: ")
    ok = verify_secret(word, stored)
    print("MATCH" if ok else "NO MATCH")
    return ok

#Encryption functions
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
    args = sys.argv[1:]
    try:
        if args == ["init-key"]:
            #Create our encryption key
            init_key()
        elif args == ["show"]:
            #Decrypt the value PII in the person vertice
            show()
        elif args and args[0] == "verify" and len(args) in (2, 3):
            #Check the hash values match, otherwise pass a 1 for incorrect
            # value
            raise SystemExit(0 if verify(*args[1:]) else 1)
        else:
            #Pass a 2 if the usage of this class was wrong (Bad parameters,
            # etc.)
            print(__doc__)
            raise SystemExit(2)
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
