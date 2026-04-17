from pathlib import Path
import hashlib
import yaml

from ..constants import config
from .models import Bin
from ..errors import BinNotFoundError


class BinLoader:
    def __init__(self, bins_path=None):
        self.bins_path = Path(bins_path or config.BINS_PATH)

    def load(self, bin_name: str) -> Bin:
        bin_path = self.bins_path / f"{bin_name}.yaml"

        if not bin_path.exists():
            raise BinNotFoundError(bin=bin_name)

        content = bin_path.read_text(encoding=config.FILE_ENCODING_UTF8)
        raw = yaml.safe_load(content) or {}
        hash_value = hashlib.sha256(content.encode()).hexdigest()

        return Bin.from_dict(raw, hash_value)

    def list(self) -> list[str]:
        return [path.stem for path in self.bins_path.glob("*.yaml")]