class Bag:
    def __init__(self):
        self.content = {}

    def _safe_path_part(self, value):
        forbidden = '<>:"/\\|?*'
        result = str(value)
        for char in forbidden:
            result = result.replace(char, "_")
        return result.strip() or "_"

    def _params_key(self, params):
        if not params:
            return "_"

        parts = []
        for key in sorted(params):
            safe_key = self._safe_path_part(key)
            safe_value = self._safe_path_part(params[key])
            parts.append(f"{safe_key}={safe_value}")

        return ",".join(parts)

    def _record_key(self, params, lang):
        return f"{self._safe_path_part(lang)}::{self._params_key(params)}"

    def stash(self, bin_name, endpoint, record):
        self.content.setdefault(bin_name, {}).setdefault(endpoint, {})
        key = self._record_key(record.params, record.lang)
        self.content[bin_name][endpoint][key] = record

    def get(self, bin_name, endpoint, *, params, lang):
        key = self._record_key(params, lang)
        return self.content.get(bin_name, {}).get(endpoint, {}).get(key)

    def has(self, bin_name, endpoint, *, params, lang):
        return self.get(bin_name, endpoint, params=params, lang=lang) is not None

    def _matches_params(self, record, query_params):
        for key, value in (query_params or {}).items():
            if str(record.params.get(key)) != value:
                return False
        return True

    def find(self, *, bin_filter=None, endpoint_filter=None, lang=None, query_params=None):
        results = []
        for bin_name, endpoints_map in self.content.items():
            if bin_filter is not None and bin_name not in bin_filter:
                continue
            for endpoint_name, records_map in endpoints_map.items():
                if endpoint_filter is not None and endpoint_name not in endpoint_filter:
                    continue
                for record in records_map.values():
                    if lang is not None and record.lang != lang:
                        continue
                    if not self._matches_params(record, query_params):
                        continue
                    results.append({
                        "bin": bin_name,
                        "endpoint": endpoint_name,
                        "record": record,
                    })
        return results

    def has_records(self, **filters):
        return bool(self.find(**filters))

    def first_lang(self, *, bin_filter=None, endpoint_filter=None, query_params=None):
        for item in self.find(
            bin_filter=bin_filter,
            endpoint_filter=endpoint_filter,
            query_params=query_params,
        ):
            return item["record"].lang
        return None

    def delete_endpoint(self, bin_name, endpoint):
        if bin_name in self.content and endpoint in self.content[bin_name]:
            self.content[bin_name].pop(endpoint, None)
            if not self.content[bin_name]:
                self.content.pop(bin_name, None)