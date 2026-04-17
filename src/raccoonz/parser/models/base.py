from abc import ABC, abstractmethod
from typing import Any
import raccoonz.constants.bin_keys as bin_keys


class BaseParser(ABC):

    @abstractmethod
    def parse(self, data: Any, fields: dict, careless: bool = False) -> dict:
        pass

    @abstractmethod
    def _select(self, source, key, value, errors):
        pass

    @abstractmethod
    def _extract(self, elements, value):
        pass

    @abstractmethod
    def _filter(self, values, value):
        pass

    @abstractmethod
    def _type(self, values, value):
        pass

    @abstractmethod
    def _select_items(self, source, key, config, errors):
        pass

    def _pipeline(self):
        return (
            self._extract,
            self._filter,
            self._type
        )

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

    def _dispatch_node(self, source, key, value, errors):
        if isinstance(value, dict) and bin_keys.OPERATOR_GROUP in value:
            return self._parse_group(source, key, value, errors)

        if isinstance(value, dict) and bin_keys.OPERATOR_MAP in value:
            return self._parse_map(source, key, value, errors)

        return self._parse_field(source, key, value, errors)

    def _parse_field(self, source, key, value, errors):
        current = self._select(source, key, value, errors)

        if not current:
            return None

        for step in self._pipeline():
            current = step(current, value)

            if current is None:
                return None

        return current

    def _parse_record(self, source, fields, errors):
        record = {}

        for child_key, child_value in fields.items():
            current = self._dispatch_node(source, child_key, child_value, errors)
            record[child_key] = self._finalize_value(current)

        return record

    def _parse_many(self, items, fields, errors):
        records = []

        for item in items:
            record = self._parse_record(item, fields, errors)

            if any(v is not None for v in record.values()):
                records.append(record)

        return records or None

    def _parse_group(self, source, key, value, errors):
        group_conf = value[bin_keys.OPERATOR_GROUP]
        item_fields = group_conf.get(bin_keys.FIELDS, {})
        items = self._select_items(source, key, group_conf, errors)

        if not items:
            return None

        return self._parse_many(items, item_fields, errors)

    def _parse_map(self, source, key, value, errors):
        map_conf = value[bin_keys.OPERATOR_MAP]

        items = self._select_items(source, key, map_conf, errors)
        if not items:
            return None

        key_conf = map_conf.get(bin_keys.OPERATOR_KEY)
        value_conf = map_conf.get(bin_keys.OPERATOR_VALUE)

        if not key_conf or not value_conf:
            errors.append(f"Incomplete _map config for field: {key}")
            return None

        result = {}

        for item in items:
            current_key = self._parse_field(
                item,
                f"{key}.{bin_keys.OPERATOR_KEY}",
                key_conf,
                errors
            )
            current_key = self._finalize_value(current_key)

            if not current_key:
                continue

            map_key = current_key

            if isinstance(value_conf, dict) and bin_keys.OPERATOR_GROUP in value_conf:
                map_value = self._parse_group(item, f"{key}.{map_key}", value_conf, errors)
            elif isinstance(value_conf, dict) and bin_keys.OPERATOR_MAP in value_conf:
                map_value = self._parse_map(item, f"{key}.{map_key}", value_conf, errors)
            else:
                map_value = self._parse_field(item, f"{key}.{map_key}", value_conf, errors)
                map_value = self._finalize_value(map_value)

            result[map_key] = map_value

        return result or None

    def _finalize_value(self, current):
        if current is None:
            return None

        if isinstance(current, list):
            if len(current) == 0:
                return None
            if len(current) == 1:
                return current[0]

        return current

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
            bin_keys.OPERATOR_MAP,
        }

        return not any(k in value for k in config_keys)