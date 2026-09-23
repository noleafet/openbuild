import json
import re

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


class ProjectEnvironment:
    env_config_path = Path(__file__).parent / "data" / "env.json"

    def __init__(self, repo_root: str | Path = REPO_ROOT, env_config_path: str | Path | None = None) -> None:
        self.repo_root = Path(repo_root)
        config_path = Path(env_config_path) if env_config_path is not None else self.env_config_path
        with config_path.open("r", encoding="utf-8") as env_file:
            self.env_config = json.load(env_file)
        self.category_env_keys = self.env_config["category_env_keys"]
        self.default_folder_aliases = self.env_config["default_folder_aliases"]

    def normalize_compose_var_name(self, filename: str | Path) -> str:
        file_name = Path(filename).name
        normalized = re.sub(r"(?i)\.ya?ml$", "", file_name)
        normalized = re.sub(r"(?i)_compose$", "", normalized)
        normalized = re.sub(r"[^A-Za-z0-9]+", "_", normalized)
        parts = [part for part in normalized.split("_") if part]
        tokens = []
        for part in parts:
            upper = part.upper()
            if upper in {"ALPINE", "UBUNTU", "DISTROLESS", "COMPOSE", "JDK", "LATEST", "LTS", "STABLE", "CE", "RHEL9"}:
                continue
            tokens.append(upper)

        if not tokens:
            return "COMPOSE"

        return "_".join(tokens)

    def canonical_tool_name(self, folder_name: str) -> str:
        alias = self.default_folder_aliases.get(folder_name)
        if alias:
            return alias

        parts = folder_name.split("_")
        filtered = [part for part in parts if part]
        if filtered and filtered[0].isdigit():
            filtered = filtered[1:]
        if len(filtered) > 1 and filtered[0] in {"SQL", "ELK"}:
            filtered = filtered[1:]
        return filtered[-1].upper() if filtered else folder_name.upper()

    def parse_devops_folder(self, folder_name: str) -> tuple[str, str]:
        prefix, _, suffix = folder_name.partition("_")
        if prefix in self.category_env_keys:
            return prefix, suffix
        return "", folder_name

    def load_env_config(self, section: str) -> list[str]:
        return self.env_config[section]

