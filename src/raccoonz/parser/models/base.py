from abc import ABC, abstractmethod
from typing import Any
import raccoonz.constants.bin_keys as bin_keys


class BaseParser(ABC):


    @abstractmethod
    def parse(self, data: Any, fields: dict, careless: bool=False) -> dict:
        pass

    
    @abstractmethod
    def _select(self, source, key, value, errors):
        pass

    @abstractmethod
    def _extract(self, elements, value):
        pass

    @abstractmethod
    def _filter(self):
        pass

    @abstractmethod
    def _type(self):
        pass


    # recursive reading
    def _walk(self, node, callback, path=""):
        result = {}

        for key, value in node.items():
            full_key = f"{path}.{key}" if path else key

            if self._is_leaf(value):
                result[key] = callback(full_key, value)

            elif self._is_branch(value):
                result[key] = self._walk(value, callback, full_key)

            else:
                result[key] = None

        return result


    def _is_leaf(self, value):
        if not isinstance(value, dict):
            return False

        return any(k in value for k in (
            bin_keys.OPERATOR_SELECT,
            bin_keys.OPERATOR_GROUP,
            bin_keys.OPERATOR_MAP
        ))


    def _is_branch(self, value):
        if not isinstance(value, dict):
            return False

        config_keys = {
            bin_keys.OPERATOR_SELECT,
            bin_keys.OPERATOR_EXTRACT,
            bin_keys.OPERATOR_FILTER,
            bin_keys.OPERATOR_TYPE,
            bin_keys.OPERATOR_GROUP,
        }

        return not any(k in value for k in config_keys)