import re

from ..constants import bin_keys
from ..constants import config


class Sniffer:
    def __init__(self, load_bin, list_bins, dig=None):
        self._load_bin = load_bin
        self._list_bins = list_bins
        self._dig = dig

    def sniff(self, url: str, *, dig=False, lang=config.PLAYWRIGHT_CONTEXT_LOCALE):
        matches = []

        url_base, url_path = self._split_base_and_path(url)

        for bin_name in self._list_bins():
            bin_data = self._load_bin(bin_name)
            bin_config = bin_data[config.BIN_CONFIG]

            base_url = bin_config.get(bin_keys.URL, "")
            endpoints = bin_config.get(bin_keys.ENDPOINTS, {})

            if not self._base_matches(url_base, base_url):
                continue

            for endpoint_name, endpoint_config in endpoints.items():
                path = endpoint_config.get(bin_keys.ENDPOINT_PATH)
                if not path:
                    continue

                regex, keys = self._path_to_regex(path)

                match_obj = re.match(regex, url_path)
                if not match_obj:
                    continue

                endpoint_params = dict(zip(keys, match_obj.groups()))

                match = {
                    config.NEST_FIELD_BIN: bin_name,
                    config.NEST_FIELD_ENDPOINT: endpoint_name,
                    config.BAG_FIELD_PARAMS: endpoint_params,
                }

                if dig:
                    if self._dig is None:
                        raise ValueError("Dig callback is not configured")

                    match = self._dig(
                        bin_name,
                        endpoint_name,
                        refresh=False,
                        lang=lang,
                        **endpoint_params
                    )

                matches.append(match)

        return matches or None

    def _normalize_url(self, url: str):
        normalized = url.strip()
        normalized = re.sub(r"^https?://", "", normalized, flags=re.IGNORECASE)
        normalized = normalized.lstrip("/")
        normalized = normalized.rstrip("/")
        return normalized

    def _split_base_and_path(self, url: str):
        normalized = self._normalize_url(url)
        parts = normalized.split("/", 1)
        base = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else "/"
        return base, path

    def _base_matches(self, url_base: str, bin_base_url: str):
        bin_base = self._normalize_url(bin_base_url).split("/", 1)[0]

        if url_base == bin_base:
            return True

        if url_base.startswith("www.") and url_base[4:] == bin_base:
            return True

        if bin_base.startswith("www.") and bin_base[4:] == url_base:
            return True

        return False

    def _path_to_regex(self, path: str):
        keys = re.findall(r"{(.*?)}", path)
        regex = re.escape(path)

        for key in keys:
            regex = regex.replace(r"\{" + key + r"\}", r"([^/]+)")

        regex = "^" + regex.rstrip("/") + "/?$"
        return regex, keys