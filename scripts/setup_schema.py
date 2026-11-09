import json
import requests
import common

from pathlib import Path

# HUGEGRAPH_AUTH_TOKEN_SECRET = os.getenv("HUGEGRAPH_AUTH_TOKEN_SECRET")

schema_path = Path(__file__).parent.parent / "json" / "graph_schema.json"

with open(schema_path, "r", encoding="utf8") as file:
    schema = json.load(file)

def request(method, endpoint, body=None):
    return common.request(common.GRAPH_URL, method, endpoint, body)


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