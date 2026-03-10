
from pathlib import Path
import yaml

def load_config(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f)