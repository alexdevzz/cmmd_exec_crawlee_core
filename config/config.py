from pathlib import Path
import yaml

_CONFIG = None


def load_config(config_path='config.yml'):
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG

    current_dir = Path(__file__).parent
    path = current_dir / config_path
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        _CONFIG = yaml.safe_load(f)

    return _CONFIG


def get_config():
    if _CONFIG is None:
        raise RuntimeError("Configuration has not been loaded. Call load_config() method first")
    return _CONFIG
