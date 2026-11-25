"""
Usage:
    python scripts/generate_data.py [--csv FILE] [--sessions 100]
                                    [--violations 8] [--seed 42] [--replace]
"""
import argparse
import csv
import json
import random
import sys
import unicodedata
from datetime import datetime, timedelta, timezone

import common
import pii

BATCH_SIZE = 500

DEFAULT_CSV = common.ROOT_DIR / "participants.csv"
EXPECTED_PATH = common.ROOT_DIR / "data" / "expected_violations.json"

#Every vertex label this script creates
DATA_LABELS = [
    "security_event", "session", "account", "person", "permission", "role",
    "service", "device", "ip_address", "network", "department",
]

#service name : (description, hosting server)
SERVICES = {
    "email":           ("Company e-mail",                   "srv-mail"),
    "wiki":            ("Internal documentation wiki",      "srv-web"),
    "gitlab":          ("Source code repositories",         "srv-dev"),
    "ci_pipeline":     ("Build and deployment pipeline",    "srv-dev"),
    "accounting_erp":  ("Accounting and invoicing system",  "srv-fin"),
    "payroll":         ("Salary and payroll processing",    "srv-fin"),
    "hr_portal":       ("Employee records and contracts",   "srv-hr"),
    "crm":             ("Customer relationship management", "srv-web"),
    "sales_dashboard": ("Sales figures and forecasts",      "srv-web"),
    "admin_console":   ("Infrastructure administration",    "srv-ops"),
    "backup_server":   ("Backup and restore",               "srv-ops"),
}

#role name : (privilege level, [(action, service), ... etc.])
ROLES = {
    "employee":       ("low",    [("read", "wiki"), ("write", "email")]),
    "developer":      ("medium", [("write", "gitlab"), ("write", "ci_pipeline"),
                                  ("write", "wiki")]),
    "accountant":     ("medium", [("write", "accounting_erp"), ("read", "payroll")]),
    "hr_officer":     ("medium", [("write", "hr_portal"), ("write", "payroll")]),
    "sales_rep":      ("medium", [("write", "crm"), ("read", "sales_dashboard")]),
    "sysadmin":       ("high",   [("admin", "admin_console"), ("admin", "backup_server"),
                                  ("read", "gitlab"), ("read", "ci_pipeline")]),
}

#department : (roles the department gives, office network)
DEPARTMENTS = {
    "Engineering":     (["employee", "developer"],  "10.10.1.0/24"),
    "Finance":         (["employee", "accountant"], "10.10.2.0/24"),
    "Human Resources": (["employee", "hr_officer"], "10.10.3.0/24"),
    "Sales":           (["employee", "sales_rep"],  "10.10.4.0/24"),
    "IT Operations":   (["employee", "sysadmin"],   "10.10.5.0/24"),
}

#department : [Job titles]
JOB_TITLES = {
    "Engineering":     ["Software Engineer", "Senior Software Engineer", "QA Engineer"],
    "Finance":         ["Accountant", "Financial Analyst", "Controller"],
    "Human Resources": ["HR Officer", "Recruiter", "HR Manager"],
    "Sales":           ["Sales Representative", "Account Manager", "Sales Manager"],
    "IT Operations":   ["System Administrator", "Network Engineer", "IT Support"],
}

ANIMALS = ["cat", "dog", "horse", "rabbit", "owl", "fox", "dolphin", "penguin",
           "elephant", "tiger", "panda", "wolf", "otter", "hedgehog", "parrot"]

DATACENTER_NETWORK = "10.20.0.0/24"
SERVERS = ["srv-mail", "srv-web", "srv-dev", "srv-fin", "srv-hr", "srv-ops"]

#Start on a Monday
START_DATE = datetime(2026, 11, 2, tzinfo=timezone.utc)
DAYS = 19


class GraphBuilder:

    def __init__(self):
        self.vertices = []  # {"label", "properties"}
        self.edges = []     # (label, out_index, in_index)

    def vertex(self, label, **properties):
        self.vertices.append({"label": label, "properties": properties})
        return len(self.vertices) - 1

    def edge(self, label, out_index, in_index):
        self.edges.append((label, out_index, in_index))

    def insert(self):
        ids = []
        for i in range(0, len(self.vertices), BATCH_SIZE):
            ids += common.request(common.GRAPH_URL, "POST", "/graph/vertices/batch",
                                  self.vertices[i:i + BATCH_SIZE])
        if len(ids) != len(self.vertices):
            raise RuntimeError("HugeGraph returned an unexpected number of vertex ids")

        edges = [{
            "label": label,
            "outV": ids[out_index],
            "inV": ids[in_index],
            "outVLabel": self.vertices[out_index]["label"],
            "inVLabel": self.vertices[in_index]["label"],
            "properties": {},
        } for label, out_index, in_index in self.edges]

        for i in range(0, len(edges), BATCH_SIZE):
            common.request(common.GRAPH_URL, "POST", "/graph/edges/batch",
                           edges[i:i + BATCH_SIZE])
        return ids


def iso(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def ascii_slug(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "".join(c for c in text.lower() if c.isalnum())


def read_people(csv_path):
    with open(csv_path, newline="", encoding="utf-8-sig") as file:
        people = [
            (row["First name"].strip(), row["Last name"].strip())
            for row in csv.DictReader(file)
            if row.get("First name", "").strip() or row.get("Last name", "").strip()
        ]
    if not people:
        raise RuntimeError(f"No people found in {csv_path}")
    return people


def graph_has_data():
    found = common.request(common.GRAPH_URL, "GET", "/graph/vertices?label=person&limit=1")
    return bool(found and found.get("vertices"))


def delete_generated_data():
    """Delete every vertex (and with it every edge) of the data labels."""
    for label in DATA_LABELS:
        result = common.request(common.BASE_URL, "POST", "/gremlin", {
            "gremlin": f"g.V().hasLabel('{label}').drop()",
            "aliases": {"graph": "DEFAULT-hugegraph", "g": "__g_DEFAULT-hugegraph"},
        })
        if result["status"]["code"] not in (200, 204):
            raise RuntimeError(f"Could not delete {label} vertices: {result}")
        print(f"Deleted all {label} vertices")

def build(people, n_sessions, n_violations, seed):
    rng = random.Random(seed)
    g = GraphBuilder()

    networks = {cidr: g.vertex("network", cidr=cidr)
                for cidr in [DATACENTER_NETWORK] + [net for _, net in DEPARTMENTS.values()]}
    internet = g.vertex("network", cidr="0.0.0.0/0")

    servers = {}
    core_switch = g.vertex("device", name="core-switch", asset_id="NET-001",
                           status="active", type="switch")
    ip_ = g.vertex("ip_address", address="10.20.0.1", is_public="false")
    g.edge("has_ip", core_switch, ip_)
    g.edge("in_network", ip_, networks[DATACENTER_NETWORK])

    for n, server in enumerate(SERVERS, start=1):
        servers[server] = g.vertex("device", name=server, asset_id=f"SRV-{n:03d}",
                                   status="active", type="server")
        ip_ = g.vertex("ip_address", address=f"10.20.0.{10 + n}", is_public="false")
        g.edge("has_ip", servers[server], ip_)
        g.edge("in_network", ip_, networks[DATACENTER_NETWORK])
        g.edge("connected_to_device", servers[server], core_switch)

    services = {}
    for name, (description, server) in SERVICES.items():
        services[name] = g.vertex("service", name=name, description=description,
                                  status="online")
        g.edge("hosts", servers[server], services[name])

    roles, permissions, allowed_by_role = {}, {}, {}
    for role_name, (privilege, grants) in ROLES.items():
        roles[role_name] = g.vertex("role", name=role_name, privilege_level=privilege)
        allowed_by_role[role_name] = set()
        for action, service in grants:
            key = (action, service)
            if key not in permissions:
                permissions[key] = g.vertex("permission", action=action,
                                            scope=f"service:{service}")
                g.edge("applies_to", permissions[key], services[service])
            g.edge("grants_permission", roles[role_name], permissions[key])
            allowed_by_role[role_name].add(service)

    departments = {}
    for dept, (dept_roles, _) in DEPARTMENTS.items():
        departments[dept] = g.vertex("department", name=dept)
        for role_name in dept_roles:
            g.edge("gives_role", departments[dept], roles[role_name])

    dept_names = list(DEPARTMENTS)
    assignment = [dept_names[i % len(dept_names)] for i in range(len(people))]
    rng.shuffle(assignment)

    # Separate generator so adding PII does not change the rest of the dataset.
    animal_rng = random.Random(f"{seed}-animals")

    users, used_usernames, host_counter = [], set(), {}
    for n, ((first, last), dept) in enumerate(zip(people, assignment), start=1):
        dept_roles, office_net = DEPARTMENTS[dept]
        person = g.vertex("person", name=f"{first} {last}".strip(),
                          job_title=rng.choice(JOB_TITLES[dept]),
                          pii=pii.encrypt(animal_rng.choice(ANIMALS)))
        g.edge("works_in_department", person, departments[dept])

        base = ".".join(p for p in (ascii_slug(first), ascii_slug(last)) if p) or f"user{n}"
        username, suffix = base, 2
        while username in used_usernames:
            username, suffix = f"{base}{suffix}", suffix + 1
        used_usernames.add(username)

        privilege = max((ROLES[r][0] for r in dept_roles),
                        key=["low", "medium", "high"].index)
        account = g.vertex("account", account_id=f"ACC-{n:04d}", username=username,
                           type="employee", is_active="true", privilege_level=privilege)
        g.edge("has_account", person, account)
        for role_name in dept_roles:
            g.edge("has_role", account, roles[role_name])

        laptop = g.vertex("device", name=f"lt-{username}", asset_id=f"LT-{n:04d}",
                          status="active", type="laptop")
        g.edge("uses_device", person, laptop)
        host_counter[office_net] = host_counter.get(office_net, 9) + 1
        address = office_net.rsplit(".", 1)[0] + f".{host_counter[office_net]}"
        ip_ = g.vertex("ip_address", address=address, is_public="false")
        g.edge("has_ip", laptop, ip_)
        g.edge("in_network", ip_, networks[office_net])

        allowed = set().union(*(allowed_by_role[r] for r in dept_roles))
        users.append({"person": person, "account": account, "laptop": laptop,
                      "ip": ip_, "username": username, "department": dept,
                      "allowed": sorted(allowed),
                      "forbidden": sorted(set(SERVICES) - allowed)})

    violating = set(rng.sample(range(n_sessions), n_violations))
    used_pairs, expected = set(), []
    for n in range(n_sessions):
        user = rng.choice(users)
        unauthorized = n in violating
        service = rng.choice(user["forbidden"] if unauthorized else user["allowed"])

        opened = (START_DATE + timedelta(days=rng.randrange(DAYS),
                                         hours=rng.randint(7, 18),
                                         minutes=rng.randrange(60),
                                         seconds=rng.randrange(60)))
        closed = opened + timedelta(minutes=rng.randint(2, 240))
        session = g.vertex("session", date_opened=iso(opened), date_closed=iso(closed))
        g.edge("session_created_by", session, user["account"])
        g.edge("session_used_service", session, services[service])
        g.edge("session_from_device", session, user["laptop"])

        if (user["person"], service) not in used_pairs:  # edge frequency is SINGLE
            used_pairs.add((user["person"], service))
            g.edge("uses_service", user["person"], services[service])

        if unauthorized:
            expected.append({"username": user["username"], "service": service,
                             "date_opened": iso(opened)})

    for n in range(1, 13):
        user = rng.choice(users)
        moment = START_DATE + timedelta(days=rng.randrange(DAYS),
                                        hours=rng.randint(0, 23), minutes=rng.randrange(60))
        event = g.vertex("security_event", event_id=f"EV-{n:04d}",
                         event_type="login_failed", timestamp=iso(moment),
                         outcome="failure", severity_level="low")
        g.edge("causes_event", user["account"], event)
        g.edge("originated_from", event, user["ip"])
        g.edge("targeted", event, services[rng.choice(user["allowed"])])

    public_ip = g.vertex("ip_address", address="203.0.113.50", is_public="true")
    g.edge("in_network", public_ip, internet)

    expected.sort(key=lambda v: v["date_opened"])
    return g, expected


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default=DEFAULT_CSV, help="participants CSV file")
    parser.add_argument("--sessions", type=int, default=100)
    parser.add_argument("--violations", type=int, default=8,
                        help="number of sessions that use a service without permission")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--replace", action="store_true",
                        help="delete previously generated data first")
    args = parser.parse_args()

    if not 0 <= args.violations <= args.sessions:
        parser.error("--violations must be between 0 and --sessions")

    if graph_has_data():
        if not args.replace:
            print("Graph already contains data; skipping (use --replace to regenerate).")
            return
        delete_generated_data()

    people = read_people(args.csv)
    graph, expected = build(people, args.sessions, args.violations, args.seed)
    graph.insert()

    EXPECTED_PATH.parent.mkdir(exist_ok=True)
    EXPECTED_PATH.write_text(json.dumps(expected, indent=2), encoding="utf-8")

    print(f"Inserted {len(graph.vertices)} vertices and {len(graph.edges)} edges "
          f"({len(people)} people, {args.sessions} sessions, "
          f"{args.violations} unauthorized).")
    print(f"Expected violations written to {EXPECTED_PATH.relative_to(common.ROOT_DIR)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
