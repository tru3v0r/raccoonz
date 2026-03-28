from abc import ABC, abstractmethod
from typing import Any


class BaseParser(ABC):
    @abstractmethod
    def parse(self, data: Any, fields: dict, careless: bool=False) -> dict:
        pass