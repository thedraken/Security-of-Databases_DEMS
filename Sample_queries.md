# Find the violations
The query does the following:
- Get every vertice that has a label `person`
- Follow the outgoing edge `has_account` to the next vertice and names it `a`
- From the account vertice, following incoming edge `session_created_by` back to every session created by the account vertice
- For each session, go to the service that it used and name it `svc`
- Select our not filter, where it finds all vertices that do not contain a valid person session use of a service. If a valid use is found, the vertices are dropped (Not visible)
- The final section, `path()` returns the whole graph, not just the last vertex of `svc`
```
g.V().hasLabel('person').outE('has_account').inV().as('a').
  inE('session_created_by').outV().
  outE('session_used_service').inV().as('svc').
  not(select('a').out('has_role').
  out('grants_permission').out('applies_to').where(eq('svc'))).
  path()
```

