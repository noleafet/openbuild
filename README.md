# OpenBuild

(v. build-one)

OpenBuild is a local, lightweight DevOps playground designed for learning, experimenting, and composing containerized services using Docker or Podman.

Navigating the modern DevOps landscape often feels overwhelming due to tool sprawl. OpenBuild solves this by organizing common, open-source DevOps utilities by lifecycle stages, giving you a centralized sandbox to test how different technologies interact.

The goal is simple: make it effortless to explore different DevOps technologies without the friction of building massive, complex configuration stacks from scratch. With OpenBuild, you can deploy standalone services or entire toolchains instantly from a single compose file.

## What this repository contains

The project is divided into two main parts:

- `devops/` — a catalog of devops-related container definitions and lifecycle categories
- `proj/your_project/` — a sample project that wires a PostgreSQL service into a minimal compose setup


### 1. DevOps tool catalog
Under `devops/`, the repository is grouped by stage and technology area:

- `01PLAN_*` — planning tools (Confluence, Jira, Trello)
- `02CODE_*` — source control and code hosting (Git, GitHub, GitLab, Bitbucket,), database (e.g PostgreSQL)
- `03BUILD_*` — build tools (Maven, Gradle, npm, pnpm, Bazel, SBT, etc.)
- `04TEST_*` — testing tools (JUnit, Selenium, Cypress, SonarQube, Postman)
- `05RELEASE_*` — release management and CI/CD tools (GitLab CI/CD, Jenkins, CircleCI, Argo CD, Spinnaker, Octopus Deploy)
- `06DEPLOY_*` — deployment targets (Docker, Kubernetes, OpenShift, Amazon ECS)
- `07OPERATE_*` — configuration and operations tools (Ansible, Docker Compose, Podman, Terraform, Puppet, Salt, Chef)
- `08MONITOR_*` — monitoring and observability tools (Grafana, Prometheus, ELK, Splunk, Datadog, New Relic, Nagios)

### 2. Compose blueprint generation utility
The script `script/py/generate_devops_yaml.py` creates example local Compose files for many common services. It is useful as a quick way to generate local container blueprints for tools without writing every YAML file by hand.

### 3. Example app
The `proj/your_project/` folder contains:

- `build.yml` — simplified compose stack example
- `.env` — shared environment variables
- persisted data directories for services e.g. PostgreSQL, Prometheus, Grafana, and SonarQube

This is the practical example showing how a project can be deployed with one compose file instead of managing every service separately.

---

## Project example architecture

The sample tested stack in `proj/your_project/build.yml` includes:

- PostgreSQL database for the app
- SonarQube database
- SonarQube service
- Prometheus
- Grafana
- Spring Boot backend service
- Next.js frontend service

The compose file uses shared environment variables from `.env`, and the app services extend reusable service definitions from the DevOps templates in `devops/`.

### Service structure

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

---

## Quick start

### Prerequisites

- Docker Engine or Podman
- Docker Compose v2 or Podman Compose
- A local Linux/macOS environment with enough CPU and memory for the example services

### Run with Docker Compose

From the repository root:

```bash
docker compose -f build.yml up -d
```

### Run with Podman Compose

```bash
podman compose -f build.yml up -d
```

The example typically exposes these services:

- Backend Springboot: 8080
- Frontend NextJS: 3000
- PostgreSQL: 5432
- Grafana: 3010
- Prometheus: 9090
- SonarQube: 9000

---

## Environment variables

The sample app uses the `.env` file in `proj/your_project/`.

Key values include:

- `DB_USER` / `DB_PASSWORD` / `DB_NAME`
- `SONAR_DB_USER` / `SONAR_DB_PASSWORD` / `SONAR_DB_NAME`
- `GF_SECURITY_ADMIN_USER` / `GF_SECURITY_ADMIN_PASSWORD`
- `GF_HOST_PORT`
- `VOLUME_DIR`

These values are shared by the compose stacks and allow you to change database names, passwords, and exposed ports without editing each service definition manually.

---

## Why this layout is useful for learning

This repository is intentionally structured as a hands-on reference:

- It shows how containerized tool stacks are organized by function.
- It gives a realistic application example with frontend, backend, and observability services.
- It can be adapted to other projects by replacing the app build context and environment variables.

A simple pattern for using this repo in a new project is:

1. Copy the app-specific service definitions from `build.yml`.
2. Adjust the build context and Dockerfiles.
3. Map your required ports and environment variables.
4. Point the compose file at the appropriate DevOps service templates.
5. Add monitoring, database, and quality tools as needed.

---

## Folder overview

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
│       └── ...genarated_local_volume_dirs/
├── README.md
└── ...
```

---

## Notes

- Project phase repository is designed as a local learning environment, not as a production-hardened deployment blueprint.
- Docker Compose and Podman Compose use the same service definitions in most cases, but some Linux and SELinux environments may require extra volume or security flags.
- The project example is intentionally simplified so that users can adapt it to their own application architecture quickly.

---

## Summary

OpenBuild gives you a practical starting point for learning modern DevOps with real container examples. The repository is especially useful for:

- exploring containerized DevOps tooling locally
- learning Compose and environment-driven deployment
- understanding how a project can be scaffolded around multiple services
- adapting a simple app stack to a larger enterprise setup

This makes it a strong reference for developers who want to move from basic container use to real-world DevOps workflows.
