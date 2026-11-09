import pathlib
import getpass
import secrets

#Prevent bad passwords
FORBIDDEN = ("'", "\\", "\n", "\r")

def ask(prompt, secret=False, default=None):
    """Prompt until we get a value that is safe to write into .env."""
    while True:
        value = getpass.getpass(prompt) if secret else input(prompt)
        if not value and default is not None:
            return default
        if not value:
            print("Value cannot be empty.")
        elif any(c in value for c in FORBIDDEN):
            print("Value cannot contain single quotes ('), backslashes (\\) or newlines.")
        else:
            return value

print("Reminder: Run this only in root directory.")
env_file = pathlib.Path(__file__).parent.parent / ".env"
if env_file.exists():
    raise Exception(".env already exists; will not overwrite.")

port = "8080"
#port = input("Enter port used for graph database. If using default port 8080, leave empty.")
#if port == "":
#    port = "8080"

username = ask("Enter the new admin username: ")
pw = ask("Enter the new admin password: ", True)

content = f"BASE_URL='http://localhost:{port}" + "'\n" + \
    f"HUGEGRAPH_USERNAME='{username}" + "'\n" + \
    f"HUGEGRAPH_ADMIN_PASSWORD='{pw}" + "'\n" + \
    f"HUGEGRAPH_AUTH_TOKEN_SECRET='{secrets.token_hex(32)}" + "'\n"

for role, default_pw in [
    ("PROJECT_ADMIN_PASSWORD", "admin_pw"),
    #No longer used
    #("EDITOR_PASSWORD", "editor_pw"),
    ("CONTRIBUTOR_PASSWORD", "contributor_pw"),
    ("SESSION_USER_PASSWORD", "session_pw"),
    ("VIEWER_PASSWORD", "viewer_pw"),]:
    role_pw = ask(f"Enter {role}. If empty, default password is"
                  f" {default_pw}: ",
             secret=True, default=default_pw)
    content += f"{role}='" + role_pw + "'\n"
    

env_file.write_text(content)
env_file.chmod(0o600)

print("Created private .env")