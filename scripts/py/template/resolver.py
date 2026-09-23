from typing import Iterable, List, Optional, Tuple

import requests
from packaging.version import InvalidVersion, parse


class ToolVersionResolver:
    @staticmethod
    def _has_registry(repo: str) -> bool:
        registry = repo.split("/", 1)[0]
        return "." in registry or ":" in registry or registry == "localhost"

    @staticmethod
    def get_highest_matching_tag(tags_list: Iterable[str], filter_keyword: str) -> Optional[str]:
        valid_tags: List[Tuple[object, str]] = []
        is_generic_stream = filter_keyword in ["latest", "stable", "lts"]

        for tag in tags_list:
            if not is_generic_stream and filter_keyword not in tag:
                continue
            if tag in ["latest", "stable", "lts"]:
                continue
            if any(x in tag.lower() for x in ["rc", "alpha", "beta", "jenkins", "windows", "arm", "debug", "sha"]):
                continue

            clean_tag = tag.lstrip("v")
            if not is_generic_stream:
                if "-" in tag:
                    parts = tag.split("-")
                    if filter_keyword in parts[-1] or filter_keyword in parts[0]:
                        version_part = parts[0].lstrip("v") if filter_keyword != parts[0] else parts[1].lstrip("v")
                    else:
                        version_part = clean_tag.split("-")[0]
                else:
                    version_part = clean_tag.replace(filter_keyword, "")
            else:
                version_part = clean_tag.split("-")[0]

            if not version_part:
                continue

            try:
                parsed = parse(version_part)
                valid_tags.append((parsed, tag))
            except InvalidVersion:
                continue

        if valid_tags:
            valid_tags.sort(key=lambda item: item[0], reverse=True)
            return valid_tags[0][1]

        return None

    @classmethod
    def fetch_tool_version(cls, tool):
        category, name, service_name, service_directory, repo, tag_filter, ports, envs, extra = tool
        resolved_tag = tag_filter
        full_repo = ""

        if repo.startswith("quay.io"):
            clean_repo = repo.replace("quay.io/", "")
            api_url = f"https://quay.io/api/v1/repository/{clean_repo}/tag/"
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    tags_data = [tag["name"] for tag in response.json().get("tags", [])]
                    best_match = cls.get_highest_matching_tag(tags_data, tag_filter)
                    if best_match:
                        resolved_tag = best_match
            except Exception:
                pass
            full_repo = repo
        elif repo.startswith("docker.elastic.co"):
            resolved_tag = tag_filter
            full_repo = repo
        elif cls._has_registry(repo):
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
                    tags_data = [item["name"] for item in results]
                    best_match = cls.get_highest_matching_tag(tags_data, tag_filter)
                    if best_match:
                        resolved_tag = best_match
            except Exception:
                pass

        key = "".join(c for c in name if c.isalnum())
        return key, category, name, service_name, service_directory, full_repo, resolved_tag, ports, envs, extra
