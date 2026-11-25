"""
Usage:
    python scripts/report_violations.py [--record-events] [--check]

    --record-events  store each finding as a security_event vertex
                     (event_type=unauthorised_access), linked to the account,
                     the targeted service and the source IP. Safe to re-run.
    --check          compare the findings with data/expected_violations.json
                     written by generate_data.py; exit 1 on a mismatch.
"""
import argparse
import json
import sys
from datetime import datetime, timezone

import common

EXPECTED_PATH = common.ROOT_DIR / "data" / "expected_violations.json"

VIOLATIONS_QUERY = """
g.V().hasLabel('session').as('s').
  out('session_created_by').as('a').
  select('s').out('session_used_service').as('svc').
  not(select('a').out('has_role').out('grants_permission').out('applies_to').where(eq('svc'))).
  select('s', 'a', 'svc').
  project('session_id', 'date_opened', 'account_id', 'username', 'person', 'department',
          'service_id', 'service', 'ip_id', 'ip').
    by(select('s').id()).
    by(select('s').values('date_opened')).
    by(select('a').id()).
    by(select('a').values('username')).
    by(select('a').in('has_account').values('name').fold()).
    by(select('a').in('has_account').out('works_in_department').values('name').fold()).
    by(select('svc').id()).
    by(select('svc').values('name')).
    by(select('s').out('session_from_device').out('has_ip').id().fold()).
    by(select('s').out('session_from_device').out('has_ip').values('address').fold())
"""


def gremlin(query, bindings=None):
    result = common.request(common.BASE_URL, "POST", "/gremlin", {
        "gremlin": query,
        "bindings": bindings or {},
        "aliases": {"graph": "DEFAULT-hugegraph", "g": "__g_DEFAULT-hugegraph"},
    })
    return result["result"]["data"]


def first(values):
    return values[0] if values else "?"


def record_event(finding):
    event_id = f"UA-{finding['session_id']}"
    existing = gremlin("g.V().hasLabel('security_event').has('event_id', eid).count()",
                       {"eid": event_id})
    if existing and existing[0] > 0:
        return False

    event = common.request(common.GRAPH_URL, "POST", "/graph/vertices", {
        "label": "security_event",
        "properties": {
            "event_id": event_id,
            "event_type": "unauthorized_access",
            "timestamp": finding["date_opened"],
            "outcome": "success",
            "severity_level": "high",
        },
    })
    edges = [
        ("causes_event", finding["account_id"], "account", event["id"], "security_event"),
        ("targeted", event["id"], "security_event", finding["service_id"], "service"),
    ]
    if finding["ip_id"]:
        edges.append(("originated_from", event["id"], "security_event",
                      finding["ip_id"][0], "ip_address"))
    common.request(common.GRAPH_URL, "POST", "/graph/edges/batch", [
        {"label": label, "outV": out_v, "outVLabel": out_l,
         "inV": in_v, "inVLabel": in_l, "properties": {}}
        for label, out_v, out_l, in_v, in_l in edges
    ])
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--record-events", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    findings = sorted(gremlin(VIOLATIONS_QUERY), key=lambda f: f["date_opened"])

    print(f"Unauthorized access report ({datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC)")
    print(f"{len(findings)} session(s) used a service without a matching permission\n")
    if findings:
        header = f"{'Opened':<21} {'User':<26} {'Department':<16} {'Service':<16} {'Source IP'}"
        print(header)
        print("-" * len(header))
    for f in findings:
        print(f"{f['date_opened']:<21} {f['username']:<26} {first(f['department']):<16} "
              f"{f['service']:<16} {first(f['ip'])}")

    if args.record_events:
        created = sum(record_event(f) for f in findings)
        print(f"\nRecorded {created} new security_event(s) "
              f"({len(findings) - created} already recorded).")

    if args.check:
        expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))
        key = lambda v: (v["username"], v["service"], v["date_opened"])
        found_keys = {key(f) for f in findings}
        expected_keys = {key(v) for v in expected}
        if found_keys == expected_keys:
            print(f"\nCHECK OK: findings match the {len(expected)} planted violations.")
        else:
            print("\nCHECK FAILED")
            for k in sorted(expected_keys - found_keys):
                print("  missed:", k)
            for k in sorted(found_keys - expected_keys):
                print("  unexpected:", k)
            raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
