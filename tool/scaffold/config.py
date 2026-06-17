from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULTS_PATH = ROOT / "config" / "scaffold_defaults.yaml"


def load_scaffold_defaults() -> dict:
    if not DEFAULTS_PATH.exists():
        return {}
    with open(DEFAULTS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_springboot_defaults() -> dict:
    return load_scaffold_defaults().get("springboot", {})
