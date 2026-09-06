# /// script
# dependencies = [
#     "requests",
#     "packaging",
# ]
# ///

from concurrent.futures import ThreadPoolExecutor
import os
import re
import requests
from packaging.version import parse, InvalidVersion

BASE_OUTPUT_DIR = '../../devops'

# Format: (Category, Display Name, Service Name, Service Directory, Registry Repo, Tag Filter, Ports list, Environment dict, Extra Config dict)
TOOLS = [
    ("01PLAN", "Confluence Server", "confluence_server", "confluence", "atlassian/confluence-server", "latest", ["8090:8090", "8091:8091"], {}, {"volumes": ["${VOLUME_DIR}/confluence_data:/var/atlassian/application-data/confluence"]}),
    ("01PLAN", "Jira Software", "jira", "jira", "atlassian/jira-software", "latest", ["8080:8080"], {}, {"volumes": ["${VOLUME_DIR}/jira_data:/var/atlassian/application-data/jira"]}),
    ("02CODE", "Git Client", "git_client", "git", "alpine/git", "latest", [], {}, {"volumes": ["./workspace:/git"]}),
    ("02CODE", "GitLab CE", "gitlab", "gitlab", "gitlab/gitlab-ce", "latest", ["443:443", "80:80", "222:22"], {}, {"volumes": ["${VOLUME_DIR}/gitlab_config:/etc/gitlab", "${VOLUME_DIR}/gitlab_logs:/var/log/gitlab", "${VOLUME_DIR}/gitlab_data:/var/opt/gitlab"]}),
    ("02CODE", "Bitbucket Server", "bitbucket", "bitbucket", "atlassian/bitbucket-server", "latest", ["7990:7990", "7999:7999"], {}, {"volumes": ["${VOLUME_DIR}/bitbucket_data:/var/atlassian/application-data/bitbucket"]}),
    ("02CODE", "PostgreSQL", "postgres_db", "sql_postgres", "library/postgres", "alpine", ["5432:5432"], {
        "POSTGRES_USER": "${DB_USER}",
        "POSTGRES_PASSWORD": "${DB_PASSWORD}",
        "POSTGRES_DB": "${DB_NAME}"
    }, {"volumes": ["postgres_data:/var/lib/postgresql/data"]}),
    ("03BUILD", "Maven", "maven", "maven", "library/maven", "alpine", [], {}, {"volumes": ["${MAVEN_WORKSPACE}:/usr/src/app", "~/.m2:/root/.m2"]}),
    ("03BUILD", "Gradle", "gradle", "gradle", "library/gradle", "jdk", [], {}, {"volumes": ["${GRADLE_WORKSPACE}:/home/gradle/project"]}),
    ("03BUILD", "Node (npm/pnpm)", "node_npm", "npm", "library/node", "alpine", [], {}, {"volumes": ["${NODE_WORKSPACE}:/usr/src/app"]}),
    ("04TEST", "Cypress Included", "cypress", "cypress", "cypress/included", "latest", [], {}, {"volumes": ["${CYPRESS_WORKSPACE}:/e2e"]}),
    ("04TEST", "SonarQube (LTS)", "sonarqube", "sonarqube", "library/sonarqube", "lts-community", ["9000:9000"], {}, {"volumes": ["${VOLUME_DIR}/sonarqube_data:/opt/sonarqube/data", "${VOLUME_DIR}/sonarqube_extensions:/opt/sonarqube/extensions"]}),
    ("04TEST", "Postman Newman", "postman", "postman", "postman/newman", "alpine", [], {}, {"volumes": ["./tests:/etc/newman"]}),
    ("05RELEASE", "Jenkins (LTS)", "jenkins", "jenkins", "library/jenkins/jenkins", "lts", ["8081:8080", "50000:50000"], {}, {"privileged": True, "user": "root", "volumes": ["${VOLUME_DIR}/jenkins_data:/var/jenkins_home", "/var/run/docker.sock:/var/run/docker.sock"]}),
    ("05RELEASE", "ArgoCD", "argocd", "argocd", "argoproj/argocd", "stable", ["8082:8080"], {}, {}),
    ("05RELEASE", "GitLab Runner", "gitlab_runner", "gitlab", "gitlab/gitlab-runner", "alpine", [], {}, {"volumes": ["/var/run/docker.sock:/var/run/docker.sock", "${VOLUME_DIR}/gitlab_runner_config:/etc/gitlab-runner"]}),
    ("06DEPLOY", "Kubernetes CLI", "kubectl", "kubernetes", "bitnami/kubectl", "latest", [], {}, {"volumes": ["~/.kube:/root/.kube"]}),
    ("06DEPLOY", "OpenShift CLI", "openshift_cli", "openshift", "openshift/origin-cli", "latest", [], {}, {}),
    ("07OPERATE", "Ansible Runner", "ansible", "ansible", "ansible/ansible-runner", "latest", [], {}, {"volumes": ["${VOLUME_DIR}/ansible:/runner"]}),
    ("07OPERATE", "Terraform", "terraform", "terraform", "hashicorp/terraform", "latest", [], {}, {"volumes": ["${VOLUME_DIR}/terraform:/workspace"]}),
    ("08MONITOR", "Grafana", "grafana", "grafana", "grafana/grafana", "latest", ["3000:3000"], {}, {"volumes": ["${VOLUME_DIR}/grafana_data:/var/lib/grafana"]}),
    ("08MONITOR", "Prometheus", "prometheus", "prometheus", "prom/prometheus", "latest", ["9090:9090"], {}, {"volumes": ["${VOLUME_DIR}/prometheus:/etc/prometheus", "${VOLUME_DIR}/prometheus_data:/prometheus"]}),
    ("08MONITOR", "Elasticsearch", "elasticsearch", "elk_elasticsearch", "elasticsearch/elasticsearch", "8.12.0", ["9200:9200"], {
        "discovery.type": "single-node",
        "xpack.security.enabled": "false"
    }, {"volumes": ["${VOLUME_DIR}/elasticsearch_data:/usr/share/elasticsearch/data"]}),
    ("08MONITOR", "Logstash", "logstash", "elk_logstash", "logstash/logstash", "8.12.0", [], {}, {"volumes": ["${VOLUME_DIR}/logstash:/usr/share/logstash/pipeline"]}),
    ("08MONITOR", "Kibana", "kibana", "elk_kibana", "kibana/kibana", "8.12.0", ["5601:5601"], {}, {}),
    ("08MONITOR", "Splunk Heavy Forwarder", "splunk", "splunk", "splunk/splunk", "latest", ["8000:8000"], {
        "SPLUNK_START_ARGS": "--accept-license",
        "SPLUNK_PASSWORD": "${SPLUNK_PASSWORD}"
    }, {"volumes": ["${VOLUME_DIR}/splunk_data:/opt/splunk/var", "${VOLUME_DIR}/splunk_etc:/opt/splunk/etc"]}),
    ("08MONITOR", "Datadog Agent", "datadog", "datadog", "datadog/agent", "latest", [], {
        "DD_API_KEY": "${DD_API_KEY}",
        "DD_SITE": "${DD_SITE}"
    }, {"volumes": ["/var/run/docker.sock:/var/run/docker.sock:ro", "${VOLUME_DIR}/proc/:/host/proc/:ro", "/sys/fs/cgroup/:/host/sys/fs/cgroup:ro"]})
]

def get_highest_matching_tag(tags_list, filter_keyword):
    valid_tags = []
    is_generic_stream = filter_keyword in ["latest", "stable", "lts"]

    for tag in tags_list:
        if not is_generic_stream and filter_keyword not in tag:
            continue
        if tag in ["latest", "stable", "lts"]:
            continue
        if any(x in tag.lower() for x in ["rc", "alpha", "beta", "jenkins", "windows", "arm", "debug", "sha"]):
            continue
        
        clean_tag = tag.lstrip('v')
        if not is_generic_stream:
            if '-' in tag:
                parts = tag.split('-')
                if filter_keyword in parts[-1] or filter_keyword in parts[0]:
                    version_part = parts[0].lstrip('v') if filter_keyword != parts[0] else parts[1].lstrip('v')
                else:
                    version_part = clean_tag.split('-')[0]
            else:
                version_part = clean_tag.replace(filter_keyword, '')
        else:
            version_part = clean_tag.split('-')[0]

        if not version_part:
            continue
            
        try:
            parsed = parse(version_part)
            valid_tags.append((parsed, tag))
        except InvalidVersion:
            continue
            
    if valid_tags:
        valid_tags.sort(key=lambda x: x[0], reverse=True)
        return valid_tags[0][1]
        
    return None

def fetch_tool_version(tool):
    category, name, service_name, service_directory, repo, tag_filter, ports, envs, extra = tool
    resolved_tag = tag_filter
    full_repo = ""

    if repo.startswith("quay.io"):
        clean_repo = repo.replace("quay.io/", "")
        api_url = f"https://quay.io/api/v1/repository/{clean_repo}/tag/"
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                tags_data = [t["name"] for t in response.json().get("tags", [])]
                best_match = get_highest_matching_tag(tags_data, tag_filter)
                if best_match:
                    resolved_tag = best_match
        except Exception:
            pass
        full_repo = repo
    elif repo.startswith("docker.elastic.co"):
        resolved_tag = tag_filter
        full_repo = repo
    else:
        if "/" not in repo:
            api_repo = f"library/{repo}"
            full_repo = f"docker.io/library/{repo}"
        else:
            api_repo = repo
            full_repo = f"docker.io/{repo}"

        api_url = f"https://hub.docker.com/v2/repositories/{api_repo}/tags/?page_size=100"
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                results = response.json().get("results", [])
                tags_data = [r["name"] for r in results]
                
                best_match = get_highest_matching_tag(tags_data, tag_filter)
                if best_match:
                    resolved_tag = best_match
        except Exception:
            pass

    key = "".join(c for c in name if c.isalnum())
    return key, category, name, service_name, service_directory, full_repo, resolved_tag, ports, envs, extra

def clean_tag(tag: str) -> str:
  return re.sub(r"[ (),\-/.]+", "_", tag.lower())

def main():
    print("=== Starting DevOps Tool Actual Version Resolver ===")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_tool_version, TOOLS))

    tags = {}
    full_repos = {}
    tool_meta = {}

    for key, category, name, service_name, service_directory, full_repo, resolved_tag, ports, envs, extra in results:
        tags[key] = resolved_tag
        full_repos[key] = full_repo
        tool_meta[key] = {
            "category": category,
            "name": name,
            "service_name": service_name,
            "service_directory": service_directory,
            "ports": ports,
            "envs": envs,
            "extra": extra
        }
        print(f"Resolved {name} ({full_repo}:{resolved_tag})")

    print(f"\nGenerating yaml files...")

    for key, meta in tool_meta.items():
        compose_lines = [
            "services:"
        ]

        image_repo = full_repos[key]
        image_version = tags[key]
        image_tag = clean_tag(image_version)
        service_name = meta["service_name"]

        compose_lines.append(f"  {service_name}:")
        compose_lines.append(f"    image: {image_repo}:{image_version}")
        
        if meta["extra"].get("privileged"):
            compose_lines.append("    privileged: true")
        if meta["extra"].get("user"):
            compose_lines.append(f"    user: {meta['extra']['user']}")

        if meta["ports"]:
            compose_lines.append("    ports:")
            for p in meta["ports"]:
                compose_lines.append(f"      - \"{p}\"")

        if meta["envs"]:
            compose_lines.append("    environment:")
            for k, v in meta["envs"].items():
                if v.startswith("--") or v == "single-node" or v == "false":
                    compose_lines.append(f"      - {k}={v}")
                else:
                    compose_lines.append(f"      {k}: {v}")

        volumes = meta["extra"].get("volumes")
        if volumes:
            compose_lines.append("    volumes:")
            for v_item in volumes:
                compose_lines.append(f"      - {v_item}")

        compose_lines.append("")

        output_dir = f"{BASE_OUTPUT_DIR}/{meta["category"].upper()}_{meta["service_directory"].upper()}"
        os.makedirs(output_dir, exist_ok=True)

        output_file = f"{output_dir}/{service_name}_{image_tag}_compose.yml"

        with open(output_file, "w") as f:
            f.write("\n".join(compose_lines) + "\n")

        print(f"Success! Manifest file generated: {output_file}")

if __name__ == "__main__":
    main()