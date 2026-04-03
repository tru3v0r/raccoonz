from .base import BaseParser
from bs4 import BeautifulSoup
import raccoonz.constants.bin_keys as bin_keys
import raccoonz.constants.config as config
from raccoonz.errors import SelectorSyntaxError
import re



class BS4Parser(BaseParser):


    def __init__(self, config=None, **kwargs):
        super().__init__()
        self.filters = (config or {}).get(bin_keys.FIELD_FILTERS, {})


    def parse(self, html, fields, careless=False):
        soup = BeautifulSoup(html, "html.parser")
        errors = []

        def parse_leaf(key, value):
            current = self._select(soup, key, value, errors)

            if not current:
                errors.append(f"Missing field: {key}")
                return None

            for step in (self._extract, self._filter):
                current = step(current, value)

                if current is None:
                    errors.append(f"Missing field: {key}")
                    return None

            return current

        result = self._walk(fields, parse_leaf)
        result[config.RESULT_ERRORS] = errors
        return result


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


    #pipeline

    def _select(self, soup, key, value, errors):
        selectors = value.get(bin_keys.FIELD_SELECT, {}).get(bin_keys.FIELD_SELECT_CSS, [])

        for selector in selectors:
            print(f"selector: {selector}")

            if not selector:
                errors.append(f"Empty selector for field: {key}")
                continue

            try:
                elements = soup.select(selector)
            except Exception:
                errors.append(f"Invalid selector for field '{key}': {selector}")
                continue

            if elements:
                return elements

        return None


    def _extract(self, elements, value):
        extract = value.get(bin_keys.FIELD_EXTRACT, bin_keys.FIELD_EXTRACT_INNER_TEXT)

        if extract == bin_keys.FIELD_EXTRACT_INNER_TEXT:
            values = [e.get_text(strip=True) for e in elements]

        elif isinstance(extract, dict) and "attr" in extract:
            attr = extract["attr"]
            values = [e.get(attr) for e in elements]

        else:
            values = []

        values = [v for v in values if v is not None]
        return values


    def _filter(self, values, value):
        filter_name = value.get(bin_keys.FIELD_FILTERS)

        if not filter_name:
            return values

        filter_conf = self.filters.get(filter_name)
        if not filter_conf:
            return values

        pattern = filter_conf.get(bin_keys.FIELD_FILTER_REGEX)
        if not pattern:
            return values

        regex = re.compile(pattern)

        result = []
        for v in values:
            if not v:
                continue

            match = regex.search(v)
            if match:
                result.append(match.group(1))

        return result


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
