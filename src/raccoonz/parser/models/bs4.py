from bs4 import BeautifulSoup
import re

from .base import BaseParser
import raccoonz.constants.bin_keys as bin_keys
import raccoonz.constants.config as config


class BS4Parser(BaseParser):

    def __init__(self, config=None, **kwargs):
        super().__init__()
        self.filters = (config or {}).get(bin_keys.FILTERS, {})

    def parse(self, html, fields, careless=False):
        soup = BeautifulSoup(html, "html.parser")
        errors = []

        def parse_leaf(key, value):
            current = self._dispatch_node(soup, key, value, errors)

            if current is None:
                errors.append(f"Missing field: {key}")
                return None

            return self._finalize_value(current)

        result = self._walk(fields, parse_leaf)
        result[config.RESULT_ERRORS] = errors
        return result

    def _select_elements(self, source, selectors, key, errors):
        for selector in selectors:
            if not selector:
                errors.append(f"Empty selector for field: {key}")
                continue

            try:
                elements = source.select(selector)
            except Exception:
                errors.append(f"Invalid selector for field '{key}': {selector}")
                continue

            if elements:
                return elements

        return None

    def _select_items(self, source, key, config_value, errors):
        selectors = config_value.get(bin_keys.OPERATOR_SELECT, {}).get(
            bin_keys.OPERATOR_SELECT_CSS, []
        )

        if not selectors:
            errors.append(f"Missing selectors for field: {key}")
            return None

        return self._select_elements(source, selectors, key, errors)

    def _select(self, source, key, value, errors):
        selectors = value.get(bin_keys.OPERATOR_SELECT, {}).get(
            bin_keys.OPERATOR_SELECT_CSS, []
        )
        return self._select_elements(source, selectors, key, errors)

    def _extract(self, elements, value):
        extract = value.get(
            bin_keys.OPERATOR_EXTRACT,
            bin_keys.OPERATOR_EXTRACT_INNER_TEXT
        )

        if extract == bin_keys.OPERATOR_EXTRACT_INNER_TEXT:
            values = [element.get_text(strip=True) for element in elements]

        elif isinstance(extract, dict) and bin_keys.OPERATOR_EXTRACT_ATTRIBUTE in extract:
            attr = extract[bin_keys.OPERATOR_EXTRACT_ATTRIBUTE]
            values = [element.get(attr) for element in elements]

        else:
            values = []

        values = [v for v in values if v is not None]
        return values

    def _filter(self, values, value):
        filter_name = value.get(bin_keys.OPERATOR_FILTER)

        if not filter_name:
            return values

        filter_conf = self.filters.get(filter_name)
        if not filter_conf:
            return values

        pattern = filter_conf.get(bin_keys.OPERATOR_FILTER_REGEX)
        if not pattern:
            return values

        regex = re.compile(pattern)

        result = []
        for v in values:
            if not v:
                continue

            match = regex.search(v)
            if match:
                if match.groups():
                    result.append(match.group(1))
                else:
                    result.append(match.group(0))

        return result or None

    def _type(self, values, value):
        type_name = value.get(bin_keys.OPERATOR_TYPE)

        if not type_name:
            return values

        if type_name == bin_keys.OPERATOR_TYPE_STRING:
            return [str(v) for v in values]

        if type_name == bin_keys.OPERATOR_TYPE_INT:
            result = []
            for v in values:
                try:
                    result.append(int(v))
                except (TypeError, ValueError):
                    continue
            return result or None

        if type_name == bin_keys.OPERATOR_TYPE_FLOAT:
            result = []
            for v in values:
                try:
                    result.append(float(v))
                except (TypeError, ValueError):
                    continue
            return result or None

        return values