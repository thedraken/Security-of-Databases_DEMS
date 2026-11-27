# Security-of-Databases_DEMS
This is a group project to create a graph data base for the class _Security of Databases_ at the University of Luxembourg. The database should help with asset management, session control, and investigating security incidents.\
We are using Apache Hugegraphs as an underlying DBMS, and implement a simple RBAC scheme on top of this.

## Setup
### Script setup
You can use `./full_setup.sh` to create the environment, create the docker, and then setup the DB. The steps are also broken down into:
- `scripts/setup_environment.sh`
- `scripts/create_docker.sh`
- `scripts/setup_db.sh`

Once done, the final line of the script will do a curl request, and if you see the version number, the DB is up and available to be used.

If you wish to reset everything, as running `./full_setup.sh` does not delete data, you can call `./full_setup.sh --reset` to wipe all the data. You can also equally call `./scripts/create_docker.sh --reset` if you are only running the separate create docker script.

Do not forget to make the script executable, using `chmod +x FILENAME`

#### Stop docker via script
The script `scripts/stop_docker.sh` will stop the docker image and turn the HugeGraph server off.

### Manual setup
To setup the database, you need **python3** and **Docker** already installed.

We start by creating the .env file. This file stores important local parameters: the graph url, admin username and password, and a secret token needed for Docker. We can set the .env file up with the `create_env.py` script>. This will prompt you to enter an admin username and password, as well as passwords for each of the test users. If you those later, they will use default passwords.
```
$ pip install -r scripts/requirements.txt
$ python3 scripts/create_env.py
```
Reminder: The `.env` file is a hidden file, so you can verify its creation with `ls -a`

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

We will now set up the actual graph. We start by creating the graph scheme.
```
$ python3 scripts/setup_schema.py
$ python3 scripts/setup_rbac.py
```

### Example data
`scripts/setup_db.sh` also runs `scripts/generate_data.py`, which creates example data.
It generates people with random names. 
Each person is assigned to one of 5 departments and gets an account, a laptop and the roles of their department.
Then 100 sessions are generated, 8 of which deliberately use a service the account has no permission for. The script skips if data already exists.

``` bash
$ .venv/bin/python scripts/generate_data.py --replace            # wipe and regenerate
$ .venv/bin/python scripts/generate_data.py --people 30 --sessions 200 --violations 15 --seed 7
```
The planted violations are written to `data/expected_violations.json`.

### Encrypted personal information (PII)
Each `person` has a `pii` property holding their favourite animal, encrypted with Fernet (AES + HMAC) in Python before it is sent to HugeGraph; the database only stores ciphertext.
The key is `PII_ENCRYPTION_KEY` in `.env`, created by `setup_environment.sh`. Losing the key makes the values unreadable.
```
$ .venv/bin/python scripts/pii.py show # Show the PII of each person
```

### Unauthorized access report
`scripts/report_violations.py` lists every session whose account has no `has_role` &rarr; `grants_permission` &rarr; `applies_to` path to the service it used.
```
$ .venv/bin/python scripts/report_violations.py                  # print the report
$ .venv/bin/python scripts/report_violations.py --check          # compare with the planted violations
$ .venv/bin/python scripts/report_violations.py --record-events  # store findings as security_event vertices
```

## How to use
The DBMs interface is reachable on `http://localhost:8088`. 
There are multiple ways to interact using the interface. 
- The graph scheme is shown on Graph-Overview > hugegraph
- Gremlin Queries can be executed in Graph Query > GQL Traversal
