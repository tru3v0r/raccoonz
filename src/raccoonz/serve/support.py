from ..constants import config


class ServeSupport:
    def __init__(self, bag):
        self.bag = bag

    def merge_filters(self, single, multiple):
        values = set()

        if single is not None:
            values.add(single)

        if multiple:
            values.update(multiple)

        return values or None

    def clean_query_params(self, query_params):
        query_params = dict(query_params)
        query_params.pop("lang", None)
        return query_params

    def format_records_response(self, records, *, raw=False):
        if len(records) == 1:
            record = records[0]["record"]

            if not raw:
                return record.data

            return {
                "bin": records[0]["bin"],
                "endpoint": records[0]["endpoint"],
                "lang": record.lang,
                "params": record.params,
                "timestamp": record.timestamp,
                "url": record.url,
                "data": record.data,
            }

        if not raw:
            return [item["record"].data for item in records]

        return [
            {
                "bin": item["bin"],
                "endpoint": item["endpoint"],
                "lang": item["record"].lang,
                "params": item["record"].params,
                "timestamp": item["record"].timestamp,
                "url": item["record"].url,
                "data": item["record"].data,
            }
            for item in records
        ]

    def resolve_path(self, value, parts):
        current = value

        for part in parts:
            if isinstance(current, dict):
                if part not in current:
                    raise KeyError(part)
                current = current[part]
                continue

            if isinstance(current, list):
                if part == "_count":
                    return len(current)

                if part.isdigit():
                    index = int(part) - 1
                    if index < 0 or index >= len(current):
                        raise IndexError(part)
                    current = current[index]
                    continue

                raise KeyError(part)

            raise TypeError(part)

        return current

    def resolve_served_lang(self, *, requested_lang=None, served_lang=None, bin_filter=None, endpoint_filter=None, query_params=None):
        clean_query = self.clean_query_params(query_params or {})
        candidates = []

        if requested_lang:
            candidates.append(requested_lang)

        if served_lang:
            candidates.append(served_lang)

        default_lang = getattr(config, "SERVE_DEFAULT_LANG", None)
        if default_lang:
            candidates.append(default_lang)

        for candidate in candidates:
            if self.bag.has_records(
                bin_filter=bin_filter,
                endpoint_filter=endpoint_filter,
                lang=candidate,
                query_params=clean_query
            ):
                return candidate

        return self.bag.first_lang(
            bin_filter=bin_filter,
            endpoint_filter=endpoint_filter,
            query_params=clean_query
        )