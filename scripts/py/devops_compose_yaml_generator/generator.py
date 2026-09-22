import argparse
import logging
from pathlib import Path
from typing import Iterable, Optional, Sequence

from .catalog import BASE_OUTPUT_DIR, TOOLS
from .compose import ServiceCompose
from .resolver import ToolVersionResolver

LOGGER = logging.getLogger("devops_generator")


class DevOpsYamlGenerator:
    @staticmethod
    def prepare_output_dir(output_dir: Optional[str | Path]) -> Path:
        base_dir = Path(output_dir) if output_dir is not None else BASE_OUTPUT_DIR
        resolved = base_dir.expanduser().resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    @staticmethod
    def generate_compose_files(
        output_dir: Optional[str | Path] = None,
        force: bool = False,
        tools: Optional[Iterable[tuple]] = None,
    ) -> list[str]:
        selected_tools = list(tools) if tools is not None else list(TOOLS)
        output_path = DevOpsYamlGenerator.prepare_output_dir(output_dir)

        LOGGER.info("Starting DevOps tool resolution for %s tools", len(selected_tools))

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

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Compose files for common DevOps images.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--output-dir", type=str, default=str(BASE_OUTPUT_DIR), help="Directory for generated compose files.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    try:
        DevOpsYamlGenerator.generate_compose_files(
            output_dir=args.output_dir,
            force=args.force,
        )
    except ValueError as exc:
        LOGGER.error(str(exc))
        raise SystemExit(2) from exc

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
