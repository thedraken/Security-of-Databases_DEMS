import os
import json
import base64
import requests
from dotenv import load_dotenv

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

load_dotenv(ROOT_DIR / ".env")

BASE_URL = os.getenv("BASE_URL")
USERNAME = os.getenv("HUGEGRAPH_USERNAME")
ADMIN_PASSWORD = os.getenv("HUGEGRAPH_ADMIN_PASSWORD")
# HUGEGRAPH_AUTH_TOKEN_SECRET = os.getenv("HUGEGRAPH_AUTH_TOKEN_SECRET")

if not BASE_URL:
    raise RuntimeError("Set the BASE_URL environment variable.")

if not USERNAME:
    raise RuntimeError("Set the HUGEGRAPH_USERNAME environment variable.")

if not ADMIN_PASSWORD:
    raise RuntimeError("Set the HUGEGRAPH_ADMIN_PASSWORD environment variable.")

# if not HUGEGRAPH_AUTH_TOKEN_SECRET:
#    raise RuntimeError("Set the HUGEGRAPH_AUTH_TOKEN_SECRET environment variable.")


GRAPH_URL = f"{BASE_URL}/graphspaces/DEFAULT/graphs/hugegraph"

auth = base64.b64encode(
    f"{USERNAME}:{ADMIN_PASSWORD}".encode()
).decode()

schema_path = Path(__file__).parent.parent / "json" / "graph_schema.json"

with open(schema_path, "r", encoding="utf8") as file:
    schema = json.load(file)


def request(method, endpoint, body=None):
    """
        - Send an authenticated request and check for errors.
        - inputs:
            - method: Request Type (GET, POST, ...)
            - endpoint: url endpoint (vertexlabels, ...)
            - body: json body that is being sent
        - output: 
            - response in json form or None
    """
    response = requests.request(
        method,
        f"{GRAPH_URL}{endpoint}",
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

    data =  response.json() if response.text else None
    
    if not response.ok:
        raise RuntimeError(
            f"{method} {path} -> HTTP {response.status_code}\n"
            f"{data}"
        )
    
    return data


def ensure_schema(collection, name, definition):
    """
        - Create only missing schema objects
        - inputs:
            - collection: The type of object we are adding (vertexlabels, ...)
            - name:  name we want to add
            - definition: Dictionary containing name, id_strategy and properties
    """
    endpoint = f"/schema/{collection}"

    # Check if the element already exists
    existing = request("GET", endpoint)

    for item in existing.get(collection, []):
        if item["name"] == name:
            print(f"Already exists: {collection}/{name}")
            return

    request("POST", endpoint, definition)

    print(f"Created: {collection}/{name}")


def delete_schema(collection, name):
    """
        - Delete a schema object by collection and name.
        - Input:
            - collection: Schema collection, (propertykeys, vertexlabels, ...)
            - name: Name of the schema object to delete.
    """
    endpoint = f"/schema/{collection}"

    # Check whether the object exists
    existing = request("GET", endpoint)

    for item in existing.get(collection, []):
        if item["name"] == name:
            request("DELETE", f"{endpoint}/{requests.utils.quote(name, safe='')}")
            print(f"Deleted: {collection}/{name}")
            return

    print(f"Already absent: {collection}/{name}")


def create_property_keys():
    """
        Create all property keys
    """
    for name in schema["property_keys"]:
        ensure_schema(
            collection="propertykeys",
            name=name,
            definition={
                "name": name,
                "data_type": "TEXT",
                "cardinality": "SINGLE"
            }
        )


def create_vertex_labels():
    """
        Create all vertex labels
    """
    for vertex in schema["vertices"]:
        definition = {
            "name": vertex["name"],
            "id_strategy": "AUTOMATIC",
            "properties": vertex["properties"]
        }

        ensure_schema(
            "vertexlabels",
            vertex["name"],
            definition
        )


def create_edge_labels():
    """
        Create all edge labels
    """
    for edge in schema["edges"]:
        definition = {
            "name": edge["name"],
            "source_label": edge["source_label"],
            "target_label": edge["target_label"],
            "frequency": "SINGLE"
        }

        ensure_schema(
            "edgelabels",
            edge["name"],
            definition
        )


def create_indexes():
    """
        Create all indexes
    """
    for index in schema.get("indexes", []):
        definition = {
            "name": index["name"],
            "base_type": index["base_type"],
            "base_value": index["base_value"],
            "index_type": index["index_type"],
            "fields": index["fields"]
        }

        ensure_schema(
            "indexlabels",
            index["name"],
            definition
        )

def main():
    print("Setting up Hugegraph schema from JSON...")

    create_property_keys()
    create_vertex_labels()
    create_edge_labels()
    create_indexes()

    print("Schema setup completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error))
        raise SystemExit(1)