# Report - Security of Databases

## 1. Introduction

The purpose of this graph database is the analysis of devices, sessions and incidents. 
- For device management, we model the connection to the user and their account, the services it hosts, its IP Addess, and connections between devices. This gives an overview over shared networks, IP addresses being reused, people using the same device, and reachable attack paths over devices.
- For session management, we model the edges between a session and the account used during the session, the service the session is for, involved devices. This allows for more oversight, and possibly notice one account creating a large amount of sessions, a device being used from different accounts, or sessions being created for sessions with invalid accounts.
- For incident management, we model the connection of security events to the services they stem from, the IP addresses involved, and the account causing the security event. This allows quick analyis of security events, and analysis of any patterns evolving.

By combining these three focuses into one database, we can give a more complete overview over different security measures. Being a graph database, we can efficiently traverse the data, model connections, find outliers, and create strong queries to analyze our system.

## 2. Installation & Analysis
We are using **Apache Hugegraphs**, as it fills most of our requirements: It allows for RBAC, has a (mostly) functioning free version, and allows us to add properties and types to nodes. (Compared to Resource Description Framework (RDF) which stores all information as edges, making it harder to clearly differentiate different types of data.)
Currently, we have only installed the database locally.

## 3. Design and Threats
Apache Hugegraphs offers no built-in encryption methods, which caused us to try to minimize the amount of sensitive data we store in our database. The only PII we currently store are employee names & account names. We also don't store any kind of organizational secrets or client data, which would cause great harm if used. The main threat would be the detailed overview over our technical setup, which could be exploited by an attacker.

## 4. Access Control
We use the built-in RBAC options in Apache Hugegraph and set up the following roles:

| Role | Permission | Explanation
| -------- | ------- | ------- |
| Project Admin | READ, WRITE, DELETE, EXECUTE on the entire graph | The project admin gets full access to everything |
| Contributor | READ, WRITE, EXECUTE on the entire graph | Contributor is allowed to add data to graph, but cannot remove already existing data. This limits the amount of damage that a single contributor can do. |
| Session User | READ and EXECUTE on all nodes and edges connected to sessions, WRITE only on sessions and the edges connected to sessions | The session user should only be able to interact with the data relevant for tracking services. We do the differentiation ebtween READ and WRITE rights, so that they f.ex. see the account involved in a session, but not change any data about that account. |
| Viewer | READ, EXECUTE on the entire graph | Can observe the entire graph, useful for analysis and auditing | 
