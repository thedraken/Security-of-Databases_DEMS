# Apache HugeGraph REST API & cURL Reference

This guide collects the cURL examples for the HugeGraph setup relevant
for this project.

**Note:** This documentation was fully written with ChatGPT, but all commands were tested by hand.

## 1. Connection variables and authentication

The following variables reflect the `common.py` configuration:

-   Server: `http://localhost:8080`
-   GraphSpace: `DEFAULT`
-   Graph: `hugegraph`
-   Graph API root: `/graphspaces/DEFAULT/graphs/hugegraph`
-   RBAC API root: `/graphspaces/DEFAULT/auth`

Run this once in Bash:

``` bash
BASE="http://localhost:8080"
GRAPH="$BASE/graphspaces/DEFAULT/graphs/hugegraph"
AUTH_URL="$BASE/graphspaces/DEFAULT/auth"

# Define credentials:
# Replace the credentials by whatever you want to test
# Reminder: Only the admin accounts can read the schema information
AUTH=(-u 'contributor_test:contributor_pw')

# To make unauthenticated requests instead, replace the line above with:
# AUTH=()
```

`curl -u username:password` enables HTTP Basic Authentication. For
example:

``` bash
curl -i "${AUTH[@]}" "$GRAPH/schema"
```

The account `contributor` must already exist and have the permissions
required for the operation. A user who can read graph data may not
necessarily be allowed to write data, execute Gremlin, or manage RBAC.

## 2. Server and graph checks

Check the server version:

``` bash
curl --compressed -sS "${AUTH[@]}" "$BASE/versions"
```

Retrieve the graph schema:

``` bash
curl --compressed -sS "${AUTH[@]}" "$GRAPH/schema"
```

## 3. Schema operations

The schema collections used in the project are:

-   `propertykeys`
-   `vertexlabels`
-   `edgelabels`
-   `indexlabels`

### List schema collections

``` bash
curl --compressed -sS "${AUTH[@]}" "$GRAPH/schema"

curl --compressed -sS "${AUTH[@]}" "$GRAPH/schema/propertykeys"
curl --compressed -sS "${AUTH[@]}" "$GRAPH/schema/vertexlabels"
curl --compressed -sS "${AUTH[@]}" "$GRAPH/schema/edgelabels"
curl --compressed -sS "${AUTH[@]}" "$GRAPH/schema/indexlabels"
```

### Retrieve one vertex label

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$GRAPH/schema/vertexlabels/person"
```

### Create a property key

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$GRAPH/schema/propertykeys" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "username",
    "data_type": "TEXT",
    "cardinality": "SINGLE"
  }'
```

### Create a vertex label

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$GRAPH/schema/vertexlabels" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "person",
    "id_strategy": "AUTOMATIC",
    "properties": ["username"],
    "nullable_keys": ["username"]
  }'
```

### Create an edge label

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$GRAPH/schema/edgelabels" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "works_in_department",
    "source_label": "person",
    "target_label": "department",
    "frequency": "SINGLE"
  }'
```

### Create an index label

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$GRAPH/schema/indexlabels" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "personByUsername",
    "base_type": "VERTEX_LABEL",
    "base_value": "person",
    "index_type": "SECONDARY",
    "fields": ["username"]
  }'
```

**Ordering matters:** create property keys before labels that refer to
them, and create the relevant vertex labels before edge labels that
refer to them. Adapt the examples to the actual schema definitions in
your project.

### Append properties to an existing vertex label

``` bash
curl -sS -X PUT "${AUTH[@]}" \
  "$GRAPH/schema/vertexlabels/person?action=append" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "person",
    "properties": ["username"]
  }'
```

### Delete a schema element

``` bash
curl -sS -X DELETE "${AUTH[@]}" \
  "$GRAPH/schema/vertexlabels/person"
```

Replace `vertexlabels` with `propertykeys`, `edgelabels`, or
`indexlabels` as appropriate. Deleting schema elements can affect
existing data.

## 4. Vertex operations

### Retrieve vertices

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$GRAPH/graph/vertices"
```

### Retrieve vertices by label

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$GRAPH/graph/vertices?label=person&limit=20"
```

Other labels in the generated dataset include `account`, `session`,
`service`, `security_event`, `permission`, `role`, `device`,
`ip_address`, `network`, and `department`.

### Retrieve one vertex by ID

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$GRAPH/graph/vertices/1"
```

Replace `1` with an actual vertex ID returned by HugeGraph.

### Create one vertex

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$GRAPH/graph/vertices" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "person",
    "properties": {
      "name": "John Doe",
      "job_title": "Software Engineer"
    }
  }'
```

### Create vertices in a batch

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$GRAPH/graph/vertices/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "label": "person",
      "properties": {
        "name": "John Doe",
        "job_title": "Software Engineer"
      }
    },
    {
      "label": "department",
      "properties": {
        "name": "Engineering"
      }
    }
  ]'
```

### Update vertex properties

``` bash
curl -sS -X PUT "${AUTH[@]}" \
  "$GRAPH/graph/vertices/1?action=append" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "person",
    "properties": {
      "job_title": "Senior Software Engineer"
    }
  }'
```

### Delete a vertex

``` bash
curl -sS -X DELETE "${AUTH[@]}" \
  "$GRAPH/graph/vertices/1"
```

Use a real vertex ID. Deleting a vertex also affects its incident edges.

## 5. Edge operations

The project's data-generation script creates edges with `label`, `outV`,
`inV`, `outVLabel`, `inVLabel`, and `properties`.

### Retrieve edges

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$GRAPH/graph/edges"
```

### Retrieve edges connected to a vertex

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$GRAPH/graph/edges?vertex_id=1&direction=BOTH"
```

An example filtered request:

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$GRAPH/graph/edges?vertex_id=1&direction=OUT&label=has_account"
```

Check the supported query parameters against the API version installed
on your server.

### Create one edge

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$GRAPH/graph/edges" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "works_in_department",
    "outV": "1",
    "inV": "2",
    "outVLabel": "person",
    "inVLabel": "department",
    "properties": {}
  }'
```

### Create edges in a batch

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$GRAPH/graph/edges/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "label": "works_in_department",
      "outV": "1",
      "inV": "2",
      "outVLabel": "person",
      "inVLabel": "department",
      "properties": {}
    },
    {
      "label": "has_account",
      "outV": "1",
      "inV": "3",
      "outVLabel": "person",
      "inVLabel": "account",
      "properties": {}
    }
  ]'
```

### Delete an edge

``` bash
curl -sS -X DELETE "${AUTH[@]}" \
  "$GRAPH/graph/edges/EDGE_ID?label=works_in_department"
```

Replace `EDGE_ID` with an actual edge ID.

## 6. Gremlin operations

The project's data-generation script posts Gremlin requests to the
top-level `/gremlin` endpoint. It uses these aliases:

``` json
{
  "graph": "DEFAULT-hugegraph",
  "g": "__g_DEFAULT-hugegraph"
}
```

The examples below use the same aliases.

### Count vertices

``` bash
curl --compressed -sS -X POST "${AUTH[@]}" \
  "$BASE/gremlin" \
  -H "Content-Type: application/json" \
  -d '{
    "gremlin": "g.V().count()",
    "aliases": {
      "graph": "DEFAULT-hugegraph",
      "g": "__g_DEFAULT-hugegraph"
    }
  }'
```

### Count edges

``` bash
curl --compressed -sS -X POST "${AUTH[@]}" \
  "$BASE/gremlin" \
  -H "Content-Type: application/json" \
  -d '{
    "gremlin": "g.E().count()",
    "aliases": {
      "graph": "DEFAULT-hugegraph",
      "g": "__g_DEFAULT-hugegraph"
    }
  }'
```

### Retrieve all people

``` bash
curl --compressed -sS -X POST "${AUTH[@]}" \
  "$BASE/gremlin" \
  -H "Content-Type: application/json" \
  -d '{
    "gremlin": "g.V().hasLabel(\"person\").valueMap(true)",
    "aliases": {
      "graph": "DEFAULT-hugegraph",
      "g": "__g_DEFAULT-hugegraph"
    }
  }'
```

### Retrieve all accounts

``` bash
curl --compressed -sS -X POST "${AUTH[@]}" \
  "$BASE/gremlin" \
  -H "Content-Type: application/json" \
  -d '{
    "gremlin": "g.V().hasLabel(\"account\").valueMap(true)",
    "aliases": {
      "graph": "DEFAULT-hugegraph",
      "g": "__g_DEFAULT-hugegraph"
    }
  }'
```

### Find people and their departments

``` bash
curl --compressed -sS -X POST "${AUTH[@]}" \
  "$BASE/gremlin" \
  -H "Content-Type: application/json" \
  -d '{
    "gremlin": "g.V().hasLabel(\"person\").out(\"works_in_department\").valueMap(true)",
    "aliases": {
      "graph": "DEFAULT-hugegraph",
      "g": "__g_DEFAULT-hugegraph"
    }
  }'
```

### Find accounts and their roles

``` bash
curl --compressed -sS -X POST "${AUTH[@]}" \
  "$BASE/gremlin" \
  -H "Content-Type: application/json" \
  -d '{
    "gremlin": "g.V().hasLabel(\"account\").out(\"has_role\").valueMap(true)",
    "aliases": {
      "graph": "DEFAULT-hugegraph",
      "g": "__g_DEFAULT-hugegraph"
    }
  }'
```

### Delete vertices of one label using Gremlin

> **Destructive:** this permanently deletes matching vertices and their
> incident edges.

``` bash
curl --compressed -sS -X POST "${AUTH[@]}" \
  "$BASE/gremlin" \
  -H "Content-Type: application/json" \
  -d '{
    "gremlin": "g.V().hasLabel(\"person\").drop()",
    "aliases": {
      "graph": "DEFAULT-hugegraph",
      "g": "__g_DEFAULT-hugegraph"
    }
  }'
```

The project's generator deletes its generated labels one by one:
`security_event`, `session`, `account`, `person`, `permission`, `role`,
`service`, `device`, `ip_address`, `network`, and `department`.

## 7. RBAC operations

The project's RBAC script uses five collection endpoints below the
`AUTH_URL`:

-   `/users`
-   `/groups`
-   `/targets`
-   `/belongs`
-   `/accesses`

The project code demonstrates `GET` and `POST` on these collections. The
payloads below follow the fields used by that script.

### 7.1 Users

List users:

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$AUTH_URL/users"
```

Create a user:

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$AUTH_URL/users" \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "contributor",
    "user_password": "contributor_pw"
  }'
```

The project code's create-user payload uses `user_name` and
`user_password`. Confirm item-level lookup, update, and delete routes
against the installed HugeGraph version before using them.

### 7.2 Groups

List groups:

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$BASE/auth/groups"
```

Create a group:

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$BASE/auth/groups" \
  -H "Content-Type: application/json" \
  -d '{
    "group_name": "contributors",
    "group_description": "Group for project contributors"
  }'
```

Save the returned group ID:

``` bash
GROUP_ID="PASTE_RETURNED_GROUP_ID_HERE"
```

### 7.3 Targets

List targets:

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$AUTH_URL/targets"
```

Create a target:

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$AUTH_URL/targets" \
  -H "Content-Type: application/json" \
  -d '{
    "target_name": "person_vertices",
    "target_graph": "hugegraph",
    "target_url": "localhost:8080",
    "target_resources": [
      {
        "type": "VERTEX",
        "label": "person",
        "properties": null
      }
    ]
  }'
```

Save the returned target ID:

``` bash
TARGET_ID="PASTE_RETURNED_TARGET_ID_HERE"
```

**Note:** The example `target_resources` object is illustrative. Use the
exact `target_details` structure from your RBAC setup
script/configuration. Do not assume that this sample resource object
matches every HugeGraph version or every resource policy.

### 7.4 Memberships (`belongs`)

List memberships:

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$AUTH_URL/belongs"
```

Add the contributor user to the group:

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$AUTH_URL/belongs" \
  -H "Content-Type: application/json" \
  -d "{
    \"user\": \"contributor\",
    \"group\": \"$GROUP_ID\"
  }"
```

### 7.5 Access permissions (`accesses`)

List access permissions:

``` bash
curl --compressed -sS "${AUTH[@]}" \
  "$AUTH_URL/accesses"
```

Grant `READ` permission to the group for the target:

``` bash
curl -sS -X POST "${AUTH[@]}" \
  "$AUTH_URL/accesses" \
  -H "Content-Type: application/json" \
  -d "{
    \"group\": \"$GROUP_ID\",
    \"target\": \"$TARGET_ID\",
    \"access_permission\": \"READ\"
  }"
```

The permission values and resource matching rules must be checked
against the RBAC documentation for your HugeGraph version. In
particular, do not assume that `READ` alone permits Gremlin execution or
write operations.