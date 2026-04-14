from .base import BaseParser
from bs4 import BeautifulSoup
import raccoonz.constants.bin_keys as bin_keys
import raccoonz.constants.config as config
from raccoonz.errors import SelectorSyntaxError
import re



class BS4Parser(BaseParser):


    def __init__(self, config=None, **kwargs):
        super().__init__()
        self.filters = (config or {}).get(bin_keys.FILTERS, {})



    def parse(self, html, fields, careless=False):
        soup = BeautifulSoup(html, "html.parser")
        errors = []

        def parse_leaf(key, value):
            if isinstance(value, dict) and bin_keys.CONTROL_FIELD_GROUP in value:
                current = self._parse_each(soup, key, value, errors)
                if current is None:
                    errors.append(f"Missing field: {key}")
                return current

            if isinstance(value, dict) and bin_keys.CONTROL_FIELD_MAP in value:
                current = self._parse_map(soup, key, value, errors)
                if current is None:
                    errors.append(f"Missing field: {key}")
                return current

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

    def _parse_map(self, soup, key, value, errors):
        map_conf = value[bin_keys.OPERATOR_MAP]

        item_selectors = map_conf.get(bin_keys.FIELD_SELECT, [])
        key_conf = map_conf.get(bin_keys.OPERATOR_KEY)
        value_conf = map_conf.get(bin_keys.OPERATOR_VALUE)

        if not item_selectors:
            errors.append(f"Missing map selectors for field: {key}")
            return None

        if not key_conf or not value_conf:
            errors.append(f"Incomplete _map config for field: {key}")
            return None

        items = None
        for selector in item_selectors:
            if not selector:
                continue
            try:
                elements = soup.select(selector)
            except Exception:
                errors.append(f"Invalid selector for field '{key}': {selector}")
                continue
            if elements:
                items = elements
                break

        if not items:
            return None

        result = {}

        for item in items:
            current_key = self._select(item, f"{key}._key", key_conf, errors)
            if not current_key:
                continue

            current_key = self._extract(current_key, key_conf)
            current_key = self._filter(current_key, key_conf)

            if not current_key:
                continue

            map_key = current_key[0] if isinstance(current_key, list) else current_key
            if not map_key:
                continue

            if isinstance(value_conf, dict) and bin_keys.CONTROL_FIELD_GROUP in value_conf:
                map_value = self._parse_each(item, f"{key}.{map_key}", value_conf, errors)
            else:
                map_value = self._select(item, f"{key}.{map_key}", value_conf, errors)
                if map_value:
                    map_value = self._extract(map_value, value_conf)
                    map_value = self._filter(map_value, value_conf)
                else:
                    map_value = None

            result[map_key] = map_value

        return result or None



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
        print(f"entered _filter")
        print(f"value: {value}")
        filter_name = value.get(bin_keys.FIELD_FILTER)

        print("filter_name")
        print(filter_name)

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



    def _parse_each(self, soup, key, value, errors):
        each_conf = value[bin_keys.OPERATOR_GROUP]

        item_selectors = each_conf.get(bin_keys.FIELD_SELECT, {}).get(bin_keys.FIELD_SELECT_CSS, [])
        item_fields = each_conf.get(bin_keys.FIELDS, {})

        items = None
        for selector in item_selectors:
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
                items = elements
                break

        if not items:
            return None

        records = []

        for item in items:
            record = {}

            for child_key, child_value in item_fields.items():
                current = self._select(item, child_key, child_value, errors)

                if not current:
                    record[child_key] = None
                    continue

                for step in (self._extract, self._filter):
                    current = step(current, child_value)
                    if current is None:
                        break

                if current is None or len(current) == 0:
                    record[child_key] = None
                elif len(current) == 1:
                    record[child_key] = current[0]
                else:
                    record[child_key] = current

            if any(v is not None for v in record.values()):
                records.append(record)

        return records



    def _type(self, values, value):
        return None
