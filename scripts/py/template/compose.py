import re


class ServiceCompose:
    def __init__(self, meta: dict, image_repo: str, image_version: str):
        self.meta = meta
        self.image_repo = image_repo
        self.image_version = image_version

    @staticmethod
    def clean_tag(tag: str) -> str:
        return re.sub(r"[ (),\-/.]+", "_", tag.lower())

    def render(self) -> str:
        service_name = self.meta["service_name"]
        compose_lines = [
            "services:",
            f"  {service_name}:",
            f"    image: {self.image_repo}:{self.image_version}",
            "    restart: unless-stopped",
        ]

        if self.meta["extra"].get("privileged"):
            compose_lines.append("    privileged: true")
        if self.meta["extra"].get("user"):
            compose_lines.append(f"    user: {self.meta['extra']['user']}")

        if self.meta["ports"]:
            compose_lines.append("    ports:")
            for port in self.meta["ports"]:
                compose_lines.append(f"      - \"{port}\"")

        if self.meta["envs"]:
            compose_lines.append("    environment:")
            for key, value in self.meta["envs"].items():
                if value is None:
                    continue
                value_text = str(value)
                if value_text.startswith("--") or value_text in {"single-node", "false"}:
                    compose_lines.append(f"      - {key}={value_text}")
                else:
                    compose_lines.append(f"      {key}: {value_text}")

        volumes = self.meta["extra"].get("volumes")
        if volumes:
            compose_lines.append("    volumes:")
            for volume in volumes:
                compose_lines.append(f"      - {volume}")

        compose_lines.append("")
        return "\n".join(compose_lines) + "\n"
