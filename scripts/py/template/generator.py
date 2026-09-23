import argparse
import logging
from pathlib import Path
from typing import Iterable, Optional, Sequence

from .catalog import TOOLS
from .compose import ServiceCompose
from .environment import ProjectEnvironment
from .resolver import ToolVersionResolver

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_YML_DIR = REPO_ROOT / "devops"
DEFAULT_PROJECT_ENV = REPO_ROOT / "proj" / "your_project" / ".env"

LOGGER = logging.getLogger("template_generator")

class TemplateGenerator:

    @staticmethod
    def generate_compose_files(
        output_dir: str | Path = DEFAULT_YML_DIR,
        force: bool = False,
        tools: Optional[Iterable[tuple]] = None,
    ) -> list[str]:

        selected_tools = list(tools) if tools is not None else list(TOOLS)

        LOGGER.info("Starting version resolver for %s devops tools", len(selected_tools))
        results = [ToolVersionResolver.fetch_tool_version(tool) for tool in selected_tools]

        tags = {}
        full_repos = {}
        tool_meta = {}
        generated_files = []

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
                "extra": extra,
            }
            LOGGER.info("Resolved %s (%s:%s)", name, full_repo, resolved_tag)

        output_path = Path(output_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        LOGGER.info("Generating YAML files in %s", output_path)
        for key, meta in sorted(tool_meta.items(), key=lambda item: item[1]["name"]):
            image_repo = full_repos[key]
            image_version = tags[key]
            image_tag = ServiceCompose.clean_tag(image_version)
            service_name = meta["service_name"]

            target_dir = output_path / f"{meta['category'].upper()}_{meta['service_directory'].upper()}"
            target_file = target_dir / f"{service_name}_{image_tag}_compose.yml"

            if target_file.exists() and not force:
                LOGGER.warning("Skipping existing file: %s (use --force to overwrite)", target_file)
                continue

            target_dir.mkdir(parents=True, exist_ok=True)
            target_file.write_text(ServiceCompose(meta, image_repo, image_version).render(), encoding="utf-8")
            generated_files.append(str(target_file))
            LOGGER.info("Generated manifest %s", target_file)

        return generated_files

    @staticmethod
    def generate_project_env_file(yml_dir: str | Path = DEFAULT_YML_DIR, output_file:str | Path = DEFAULT_PROJECT_ENV) -> Path:
        environment = ProjectEnvironment(repo_root=REPO_ROOT)

        lines = environment.load_env_config("openbuild_configurations")
        lines.extend(f"{env_key}={category}" for category, env_key in environment.category_env_keys.items())
        lines.append("")

        devops_root = Path(yml_dir)
        grouped: dict[str, list[str]] = {}
        for compose_file in sorted(devops_root.rglob("*_compose.yml")):
            folder_name = compose_file.parent.name
            grouped.setdefault(folder_name, []).append(compose_file.name)

        for folder_name, files in sorted(grouped.items()):
            category_key, tool_suffix = environment.parse_devops_folder(folder_name)
            if not category_key:
                category_key = "08MONITOR"
                tool_suffix = folder_name
            tool_name = environment.canonical_tool_name(tool_suffix)
            default_name = sorted(files)[0]
            default_var = f"DEVOPS_{environment.normalize_compose_var_name(default_name)}"
            lines.append(f"{default_var}={tool_suffix}/{default_name}")

            dir_default_var = f"DEVOPS_{tool_name}_DIR_DEFAULT"
            lines.append(f"{dir_default_var}=${{DEVOPS_DIR}}/${{{environment.category_env_keys.get(category_key, 'DEVOPS_MONITOR')}}}_${{{default_var}}}")
            lines.append("")

        lines.extend(environment.load_env_config("user_configurations"))

        env_content = "\n".join(lines) + "\n"

        env_file = Path(output_file)
        env_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to the file
        env_file.write_text(env_content, encoding="utf-8")
        
        return env_file


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Compose files for common DevOps images.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument(
        "--output-dir",
        "--yml-dir",
        dest="output_dir",
        type=str,
        default=str(DEFAULT_YML_DIR),
        help="Directory for generated yml files.",
    )
    parser.add_argument(
        "--project-env",
        type=str,
        default=str(DEFAULT_PROJECT_ENV),
        help="Write the generated project environment template to this path.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        TemplateGenerator.generate_compose_files(
            output_dir=args.output_dir,
            force=args.force,
        )

        TemplateGenerator.generate_project_env_file(
            yml_dir=args.output_dir, 
            output_file=args.project_env
        )

    except ValueError as exc:
        LOGGER.error(str(exc))
        raise SystemExit(2) from exc

    return 0


DevOpsYamlGenerator = TemplateGenerator


if __name__ == "__main__":
    raise SystemExit(main())
