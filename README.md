# OpenBuild

(v. build-one)

[![YAML](https://img.shields.io/badge/YAML-configuration-cb171e?logo=yaml&logoColor=white)](https://yaml.org/)
[![Podman Compose](https://img.shields.io/badge/Podman%20Compose-container%20orchestration-892ca0?logo=podman&logoColor=white)](https://docs.podman.io/en/latest/markdown/podman-compose.1.html)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-container%20orchestration-2496ed?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

OpenBuild is a local, lightweight DevOps playground designed for learning, experimenting, and composing containerized services using Docker or Podman.

Navigating the modern DevOps landscape often feels overwhelming due to tool sprawl. OpenBuild solves this by organizing common, open-source DevOps utilities by lifecycle stages, giving you a centralized sandbox to test how different technologies interact.

The goal is simple: make it effortless to explore different DevOps technologies without the friction of building massive, complex configuration stacks from scratch. With OpenBuild, you can deploy standalone services or entire toolchains instantly from a single compose file.

### What this repository contains

The repository is organized into four complementary parts:

- `devops/` — reusable Compose definitions for DevOps tools, grouped by lifecycle stage
- `proj/your_project/` — a starter project template with environment settings, Compose configuration, and local service data
- `samples/openbook/` — a complete runnable example stack based from the template
- `scripts/` — utility scripts, including the tool that generates Compose blueprints

#### Directory overview

```text
openbuild/
├── devops/
│   ├── 01PLAN_*/
│   ├── 02CODE_*/
│   ├── 03BUILD_*/
│   ├── 04TEST_*/
│   ├── 05RELEASE_*/
│   ├── 06DEPLOY_*/
│   ├── 07OPERATE_*/
│   └── 08MONITOR_*/
├── proj/
│   └── your_project/
│       ├── .env
│       ├── build.yml
│       └── ...generated_local_volume_dirs/
├── scripts/
│   ├── py/
│   │   └── generate_devops_yaml.py
│   └── ps/
│       └── pcup.ps1
├── README.md
└── ...
```


#### 1. DevOps tool catalog
The `devops/` directory groups container definitions by lifecycle stage and technology area:

- `01PLAN_*` — planning tools, such as Confluence and Jira
- `02CODE_*` — source control, code hosting, and databases, such as Git, GitLab, Bitbucket, and PostgreSQL
- `03BUILD_*` — build tools, such as Maven, Gradle, and npm
- `04TEST_*` — testing and code quality tools, such as Cypress, Postman, and SonarQube
- `05RELEASE_*` — release and CI/CD tools, such as GitLab CI/CD, Jenkins, CircleCI, Argo CD, and Octopus Deploy
- `06DEPLOY_*` — deployment targets, such as Kubernetes and OpenShift
- `07OPERATE_*` — configuration and operations tools, such as Ansible and Terraform
- `08MONITOR_*` — monitoring and observability tools, such as Grafana, Prometheus, ELK, Splunk, and Datadog


#### 2. Compose blueprint generation utility (optional)

[![Python](https://img.shields.io/badge/Python-3.x-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![uv](https://img.shields.io/badge/uv-latest-de5fe9?logo=astral&logoColor=white)](https://docs.astral.sh/uv/)

The script `scripts/py/generate_devops_yaml.py` creates example local Compose files for common services. It resolves suitable container image tags from Docker Hub and writes the generated files to `devops/`.

#### Generate DevOps Compose files

From the repository root, run the generator from its directory so its relative output path resolves to `devops/`:

```bash
cd scripts/py
uv run generate_devops_yaml.py
```

The first run may take a little longer while `uv` creates the isolated environment and installs the inline dependencies.


### 3. Example application

The `samples/openbook/` directory contains:

- `build.yml` — simplified compose stack example
- `.env` — shared environment variables
- persisted data directories for services such as PostgreSQL, Prometheus, Grafana, and SonarQube

This example shows how to deploy an application and its supporting services with one Compose file instead of managing each service separately.

#### Service structure

The sample tested stack in `samples/openbook/build.yml` includes:

- PostgreSQL database for the app
- SonarQube database
- SonarQube service
- Prometheus
- Grafana
- Spring Boot backend service
- Next.js frontend service

The compose file uses shared environment variables from `.env`, and the app services extend reusable service definitions from the DevOps templates in `devops/`.

```yaml
services:
  app_db:
    extends:
      file: ${DEVOPS_POSTGRES}
      service: postgres_db

  sonarqube_db:
    extends:
      file: ${DEVOPS_SONAR}
      service: sonarqube_db

  sonarqube:
    extends:
      file: ${DEVOPS_SONAR}
      service: sonarqube

  prometheus:
    extends:
      file: ${DEVOPS_PROMETHEUS}
      service: prometheus

  grafana:
    extends:
      file: ${DEVOPS_GRAFANA}
      service: grafana

  backend:
    build:
      context: <project_backend_location>
      dockerfile: <project_backend_dockerfile>

  frontend:
    build:
      context: <project_frontend_location>
      dockerfile: <project_frontend_dockerfile>
```

This pattern is useful for learning because it demonstrates how a single project can compose multiple services from separate infrastructure definitions while keeping the app deployment easy to read.



### Quick start

A simple pattern for using this repo in a new project is:

1. Update the template directory naming to your app.
2. Adjust the build stack and enviroments.
3. Run the build through docker / podman compose.

#### Run with Docker Compose

```bash
docker compose -f build.yml up -d
```

#### Run with Podman Compose on Linux/macOS

```bash
podman compose -f build.yml up -d
```

#### Run with Podman Compose on Windows

If Podman does not automatically create the local directories used by the bind mounts, run the PowerShell helper from the example project directory. It creates the missing volume directories before starting the stack:

```powershell
cd proj/your_project
& ../../scripts/ps/pcup.ps1
```

If PostgreSQL 18 or newer reports a permission error on Windows, uncomment `PGDATA=/mnt/postgres_win/data` in `proj/your_project/.env` and run the helper again.

The example typically exposes these services:

- Backend Springboot: 8080
- Frontend NextJS: 3000
- PostgreSQL: 5432
- Grafana: 3010
- Prometheus: 9090
- SonarQube: 9000

#### Environment variables

The sample app uses the `.env` file in `proj/your_project/`.

Key values include:

- `DB_USER` / `DB_PASSWORD` / `DB_NAME`
- `SONAR_DB_USER` / `SONAR_DB_PASSWORD` / `SONAR_DB_NAME`
- `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD`
- `GF_HOST_PORT`
- `VOLUME_DIR`

These values are shared by the compose stacks and allow you to change database names, passwords, and exposed ports without editing each service definition manually.

#### Why Grafana and Prometheus on example stack? 

Using a Grafana and Prometheus dashboard combination turns raw, text-based system metrics into clear, real-time visual charts that make infrastructure and app health easy to monitor and it can be configured in just few steps:

After starting the example stack, open Grafana at [http://localhost:3010](http://localhost:3010) and sign in with the credentials configured by `GF_SECURITY_ADMIN_USER` and `GF_SECURITY_ADMIN_PASSWORD` in `.env`.

#### Add Prometheus as a data source

1. Open **Connections > Data sources** and select **Add new data source**.
2. Select **Prometheus**.
3. Set the URL to `http://prometheus:9090`.
4. Select **Save & test**. Grafana should confirm that the Prometheus data source is working.

Use the Compose service name, `prometheus`, in the URL because Grafana connects to Prometheus over the internal container network. The published host port, `9090`, is intended for access from the host machine.

#### Import a dashboard by ID

1. Open **Dashboards > New > Import**.
2. Enter the dashboard ID from [Grafana Dashboards](https://grafana.com/grafana/dashboards/) and select **Load**.
3. Choose the Prometheus data source you created above.
4. Select **Import**.

Choose a dashboard whose required metrics are available in this Prometheus configuration. For example, dashboard ID `1860` requires Node Exporter metrics, which are not included in the default example stack.

#### Recommended application dashboard IDs

- **Spring Boot:** `4701` — JVM Micrometer. This is the best general-purpose choice for the `/actuator/prometheus` metrics exposed by the backend.

![JVM Micrometer](https://grafana.com/api/dashboards/4701/images/14220/image)

- **Next.js / Node.js:** `11159` — NodeJS Application Dashboard. The OpenBook example uses the `prom-client` library to expose default metrics through `/api/metrics`, making this dashboard suitable for the example stack.

![NodeJS Application Dashboard](https://grafana.com/api/dashboards/11159/images/7101/image)

The dashboard must match the metric names and labels emitted by the application. Importing a dashboard ID alone does not create metrics that the application or its exporter does not expose.



### Notes

- Project phase repository is designed as a local learning environment, not as a production-hardened deployment blueprint.
- Docker Compose and Podman Compose use the same service definitions in most cases, but some Linux and SELinux environments may require extra volume or security flags.
- The project example is intentionally simplified so that users can adapt it to their own application architecture quickly.



### Summary

OpenBuild gives you a practical starting point for learning modern DevOps with real container examples. The repository is especially useful for:

- exploring containerized DevOps tooling locally
- learning Compose and environment-driven deployment
- understanding how a project can be scaffolded around multiple services
- adapting a simple app stack to a larger enterprise setup

This makes it a strong reference for developers who want to move from basic container use to real-world DevOps workflows.
