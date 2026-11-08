# Security-of-Databases_DEMS
This is a group project to create a graph datsa base for the class _Security of Databases_ at the University of Luxembourg. The database should help with asset management, session control, and investigating security incidents.\
We are using Apache Hugegraphs as an underlying DBMS, and implement a simple RBAC scheme on top of this.

## Setup
To setup the database, you need **python3** and **Docker** already installed.

We start by creating the .env file. This file stores important local parameters: the graph url, admin username and password, and a secret token needed for Docker. We can set the .env file up with the `create_env.py` script>:
```
$ pip install -r scripts/requirements.txt
$ python3 scripts/create_env.py
```

Next, we need to set up the docker container. To avoid conflicts with other instances of this program, you can change the container name after `-p` to something that has not yet been used.
```
$ docker compose \
  --env-file .env \
  -p dems_hugegraph \
  -f hugegraph/docker/docker-compose.yml \
  up -d --wait
```
You can now check if the server is running:
```
$ curl http://localhost:8080/versions
```
The Hubble interface should be reachable with any browser on `http://localhost:8088`.

---
We will now set up the actual graph. We start by creating the graph scheme.
```
$ python3 scripts/setup_schema.py
```
