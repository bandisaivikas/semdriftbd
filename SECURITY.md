# Security Policy

## Supported versions

Only the latest code on the `main` branch is maintained.

## Reporting a vulnerability

Please do **not** open a public issue for security problems.

Report them privately through GitHub: go to the **Security** tab of this repository and click **Report a vulnerability**. You should get a reply within 7 days.

Include:

- what the problem is and which files it affects,
- steps to reproduce it,
- what an attacker could do with it.

## Scope

SemDriftBD is research code meant to run locally on Docker. The provided `docker-compose.yml` and `kafka-docker-compose.yml` expose Spark and Kafka on `localhost` **without authentication or encryption**. Do not expose these ports to the internet or run this setup on a shared network without adding authentication and TLS.
