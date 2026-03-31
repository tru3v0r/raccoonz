from .base import BaseParser
from bs4 import BeautifulSoup
import raccoonz.constants.bin_keys as bin_keys
from raccoonz.errors import SelectorSyntaxError



class BS4Parser(BaseParser):


    def parse(self, html, fields, careless=False):
        soup = BeautifulSoup(html, "html.parser")
        errors = []

        def parse_leaf(key, value):
            current = self._select(soup, key, value, errors)

            if not current:
                errors.append(f"Missing field: {key}")
                return None

            for step in (self._extract, self._filter, self._type):
                current = step(current, value)

                if current is None:
                    errors.append(f"Missing field: {key}")
                    return None

            return current

        result = self._walk(fields, parse_leaf)
        result["_errors"] = errors
        return result


    # recursive reading

    def _walk(self, node, callback, path=""):
        return None


    #pipeline

    def _select(self, soup, key, value, errors):
        return None


    def _extract(self, elements, value):
        return None


    def _filter(self, values, value):
        return None


    def _type(self, values, value):
        return None


    # helpers

    def _is_leaf(self, value):
        return (
            isinstance(value, dict)
            and bin_keys.FIELD_SELECT in value
        )


    def _is_branch(self, value):
        if not isinstance(value, dict):
            return False

        config_keys = {
            bin_keys.FIELD_SELECT,
            bin_keys.FIELD_EXTRACT,
            bin_keys.FIELD_FILTERS,
            bin_keys.FIELD_TYPE,
        }

        return not any(k in value for k in config_keys)
