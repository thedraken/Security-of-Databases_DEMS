import pathlib
import getpass
import secrets


print("Reminder: Run this only in root directory.")
env_file = pathlib.Path(__file__).parent.parent / ".env"
if env_file.exists():
    raise Exception(".env already exists; will not overwrite.")

port = "8080"
#port = input("Enter port used for graph database. If using default port 8080, leave empty.")
#if port == "":
#    port = "8080"

username = input("Enter the new admin username: ")
if not username or "'" in username or "\n" in username:
    raise SystemExit("Use a username without single quotes or newlines")

pw = getpass.getpass("Enter the new admin password: ")
if not pw or "'" in pw or "\n" in pw:
    raise SystemExit("Use a password without single quotes or newlines")

env_file.write_text(
    "BASE_URL='http://localhost:" + port + "'\n" + 
    "HUGEGRAPH_USERNAME='" + username + "'\n" +
    "HUGEGRAPH_ADMIN_PASSWORD='" + pw + "'\n" +
    "HUGEGRAPH_AUTH_TOKEN_SECRET='" + secrets.token_hex(32) + "'\n"
)
env_file.chmod(0o600)

print("Created private .env")