import os
import json
import common

GRAPH = "hugegraph"

GROUPS = "/auth/groups"

# JSON configuration
CONFIG_PATH = common.ROOT_DIR / "json" / "rbac.json"

with open(CONFIG_PATH, "r", encoding="utf-8") as file:
    config = json.load(file)

# ------------------------------------------------
# HTTP functions
# ------------------------------------------------

def request(method, endpoint, body=None):
    return common.request(common.BASE_URL, method, endpoint, body)


def find_existing(path, collection, key, value):
    """
    - Find an existing object by a unique field
    - Input
        - path: url
        - collection (f.ex. users)
        - key: attribute key
        - value: value of attribute
    - Output:
        - item if it exists, None else
    """
    response = request("GET", path)
    objects = response.get(collection, []) if response else []

    for item in objects:
        if item.get(key) == value:
            return item

    return None


def ensure_object(path, collection, key, value, body):
    """
        Create an object if it does not already exist.
    """
    existing = find_existing(path, collection, key, value)

    if existing:
        print(f"Already exists: {collection}/{value}")
        return existing

    created = request("POST", path, body)

    if not created or not created.get("id"):
        raise RuntimeError(
            f"Could not obtain ID of created object: {collection}/{value}"
        )

    print(f"Created: {collection}/{value}")

    return created

# ------------------------------------------------
# Create Functions
# ------------------------------------------------

## Targets

def ensure_target(target):
    """
        Create the target or return the existing target
    """
    name = target["name"]

    body = {
        "target_name": name,
        "target_graph": GRAPH,
        "target_url": common.TARGET_URL,
        "target_resources": target["target_details"]
    }

    return ensure_object(
        path=f"{common.AUTH}/targets",
        collection="targets",
        key="target_name",
        value=name,
        body=body
    )

def create_targets():
    """
        Create all targets and return their IDs.
    """
    print("\n--- Creating targets ---")

    target_ids = {}

    for target in config.get("targets", []):
        created = ensure_target(target)
        target_ids[target["name"]] = created["id"]

    return target_ids


## Groups

def ensure_group(role):
    """
        Create or reuse a group for a role
    """
    name = role["name"]

    body = {
        "group_name": name,
        "group_description": role.get(
            "description",
            f"{name} access group"
        )
    }

    return ensure_object(
        path=GROUPS,
        collection="groups",
        key="group_name",
        value=name,
        body=body
    )


def create_groups():
    """
        Create all groups and return their IDs
    """
    print("\n--- Creating groups ---")
    
    group_ids = {}

    for role in config.get("roles", []):
        created = ensure_group(role)
        group_ids[role["name"]] = created["id"]

    return group_ids


## Permissions
def ensure_permission(group_id, target_id, permission):
    """
        Grant permission to a group on a target.
    """
    path = f"{common.AUTH}/accesses"

    response = request("GET", path)

    accesses = response.get("accesses", []) if response else []

    for item in accesses:
        if (
            str(item.get("group")) == str(group_id)
            and str(item.get("target")) == str(target_id)
            and item.get("access_permission") == permission
        ):
            print(f"Permission exists: {permission} for {group_id}")
            return

    request(
        "POST",
        path,
        {
            "group": group_id,
            "target": target_id,
            "access_permission": permission
        }
    )

    print(f"Granted: {permission} for {group_id}")


def create_permissions(group_ids, target_ids):
    """
        Grant all permissions defined in the JSON config
    """

    print("\n--- Creating permissions ---")

    for role in config.get("roles", []):
        role_name = role["name"]
        group_id = group_ids[role_name]

        for permission_entry in role.get("permissions", []):
            target_name = permission_entry["target"]

            if target_name not in target_ids:
                raise RuntimeError(
                    f"Unknown target '{target_name}' "
                    f"referenced by role '{role_name}'"
                )

            target_id = target_ids[target_name]

            for permission in permission_entry["operations"]:
                ensure_permission(
                    group_id,
                    target_id,
                    permission
                )


## Users
def ensure_user(user_config):
    """
        Create or reuse a HugeGraph user.
    """

    name = user_config["name"]

    password_env = user_config.get("password_env")

    if not password_env:
        raise RuntimeError(
            f"Password environment variable missing for user {name}"
        )

    password = os.getenv(password_env)

    if not password:
        raise RuntimeError(
            f"Environment variable {password_env} "
            f"is missing or empty"
        )

    body = {
        "user_name": name,
        "user_password": password
    }

    return ensure_object(
        path=f"{common.AUTH}/users",
        collection="users",
        key="user_name",
        value=name,
        body=body
    )


def ensure_membership(user_id, group_id):
    """
        Assign a user to a group if not already assigned.
    """

    path = f"{common.AUTH}/belongs"

    response = request("GET", path)

    memberships = response.get("belongs", []) if response else []

    for item in memberships:
        if (
            str(item.get("user")) == str(user_id)
            and str(item.get("group")) == str(group_id)
        ):
            print(f"Membership exists: {user_id} -> {group_id}")
            return

    request(
        "POST",
        path,
        {
            "user": user_id,
            "group": group_id
        }
    )

    print(f"Assigned: {user_id} -> {group_id}")


def create_users(group_ids):
    """
        Create users and assign them to their configured groups.
    """

    print("\n--- Creating users and memberships ---")

    for user_config in config.get("users", []):

        username = user_config["name"]
        role_name = user_config["role"]

        if role_name not in group_ids:
            raise RuntimeError(
                f"Unknown role '{role_name}' assigned to user '{username}'"
            )

        user = ensure_user(user_config)

        group_id = group_ids[role_name]

        ensure_membership(
            user["id"],
            group_id
        )

# ------------------------------------------------
# Validate Configuration
# ------------------------------------------------

def validate_config():
    """
        Check references between targets, roles, and users
        before making API changes.
    """
    target_names = {
        target["name"]
        for target in config.get("targets", [])
    }
    
    role_names = {
        role["name"]
        for role in config.get("roles", [])
    }

    for role in config.get("roles", []):
        for entry in role.get("permissions", []):
            if entry["target"] not in target_names:
                raise RuntimeError(
                    f"Role '{role['name']}' references "
                    f"unknown target '{entry['target']}'"
                )

    for user in config.get("users", []):
        if user["role"] not in role_names:
            raise RuntimeError(
                f"User '{user['name']}' references "
                f"unknown role '{user['role']}'"
            )

# ------------------------------------------------
# Main
# ------------------------------------------------

def main():
    print("Configuring HugeGraph RBAC...\n")

    validate_config()

    target_ids = create_targets()

    group_ids = create_groups()

    create_permissions(group_ids, target_ids)

    create_users(group_ids)

    print("\nRBAC configuration completed successfully.")

if __name__ == "__main__":
    try:
        main()

    except Exception as error:
        print("\nRBAC setup failed:")
        print(error)
        raise SystemExit(1)