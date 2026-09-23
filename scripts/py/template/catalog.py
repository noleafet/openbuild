import json
from pathlib import Path

CATALOG_PATH = Path(__file__).parent / "data" / "tools.json"


class ToolCatalog:
    def __init__(self, catalog_path: str | Path | None = None):
        self.catalog_path = Path(catalog_path) if catalog_path is not None else CATALOG_PATH

    @staticmethod
    def load(catalog_path: str | Path | None = None) -> list[tuple]:
        resolved_path = Path(catalog_path) if catalog_path is not None else CATALOG_PATH
        if not resolved_path.exists():
            raise FileNotFoundError(f"Tool catalog not found: {resolved_path}")

        with resolved_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)

        if isinstance(payload, dict):
            raw_tools = payload.get("tools", [])
        else:
            raw_tools = payload

        return [tuple(tool) for tool in raw_tools]


TOOLS = ToolCatalog.load()
