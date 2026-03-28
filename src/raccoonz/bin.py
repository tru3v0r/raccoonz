import yaml
from pathlib import Path
from .errors import BinNotFoundError

def load(bin: str) ->dict:
    local_path = Path(__file__).parent / "bins" / f"{bin}.yaml"

    if local_path.exists():
        return yaml.safe_load(local_path.read_text())
    
    raise BinNotFoundError(bin=bin)