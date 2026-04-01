from pathlib import Path
from datetime import datetime
import yaml

from .constants import config
from .constants import bin_keys
from .bin import load as load_bin
from .errors import EndpointNotFoundError, BinKeyError
from .fetcher.factory import build_fetcher
from .parser.factory import build_parser



class Raccoon:


    def __init__(self, bin: str, debug: bool=False, **kwargs):
        self.bin = bin
        self.config = load_bin(bin)
        self.debug = debug

        default_fetcher = config.DEFAULT_FETCHER
        default_parser = config.DEFAULT_PARSER

        bin_fetcher = self.config.get(bin_keys.FETCHER, default_fetcher)
        bin_parser = self.config.get(bin_keys.PARSER, default_parser)

        self.fetcher = build_fetcher(bin_fetcher, **kwargs)
        self.parser = build_parser(bin_parser, config=self.config, **kwargs)

        self.bag = {}
        self.nest_root = Path(config.NEST_PATH) / self.bin


    def dig(self, endpoint, params, refresh=False):

        endpoints = self.config.get("endpoints", {})

        if endpoint not in endpoints:
            raise EndpointNotFoundError(endpoint)
        
        ep = endpoints[endpoint]

        base_url = self.config.get(bin_keys.URL)
        path = ep.get(bin_keys.ENDPOINT_PATH)

        if not base_url:
            raise BinKeyError(bin, bin_keys.URL)
        
        if not path:
            raise BinKeyError(bin, bin_keys.ENDPOINT_PATH)
        
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}".format(**params)
        params_key = self._params_key(params)

        cached = self.bag.get(endpoint, {}).get(params_key)
        if not refresh and cached and cached.get(config.BAG_FIELD_DATA) is not None:
            return cached[config.BAG_FIELD_DATA]
        
        html = self.fetcher.fetch(url)

        parsed = self.parser.parse(
            html,
            ep.get(bin_keys.FIELDS))
        
        timestamp = self._timestamp()

        # write to bag
        self._stash(
            endpoint=endpoint,
            params=params,
            url=url,
            html=html,
            data=parsed,
            timestamp=timestamp,
        )

        # write to nest
        self._hoard(
            endpoint=endpoint,
            params=params,
            html=html,
            data=parsed,
            timestamp=timestamp,
        )
        
        return parsed
    

    # write to bag

    def _stash(self, endpoint, params, url, html, data, timestamp):
        params_key = self._params_key(params)

        if endpoint not in self.bag:
            self.bag[endpoint] = {}

        self.bag[endpoint][params_key] = {
            config.BAG_FIELD_PARAMS: params,
            config.BAG_FIELD_URL: url,
            config.BAG_FIELD_HTML: html,
            config.BAG_FIELD_DATA: data,
            config.BAG_FIELD_TIMESTAMP: timestamp,
        }

    
    # write to nest

    def _hoard(self, endpoint, params, html, data, timestamp):
        raw_dir = self._raw_dir_params(endpoint, params)
        data_dir = self._data_dir_params(endpoint, params)

        raw_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        raw_path = raw_dir / f"{timestamp}.html"
        data_path = data_dir / f"{timestamp}.yaml"

        raw_path.write_text(html, encoding="utf-8")

        with data_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


    # load from nest to bag

    def _pack(self):
        endpoints = self.config.get(bin_keys.ENDPOINTS, {})

        for endpoint in endpoints:
            raw_dir = self._raw_dir_endpoint(endpoint)
            data_dir = self._data_dir_endpoint(endpoint)

            params_dirs = set()

            if raw_dir.exists():
                params_dirs.update(
                    p.name for p in raw_dir.iterdir() if p.is_dir()
                )

            if data_dir.exists():
                params_dirs.update(
                    p.name for p in data_dir.iterdir() if p.is_dir()
                )

            for params_key in params_dirs:
                raw_dir = raw_dir / params_key
                data_dir = data_dir / params_key

                raw_file = self._latest_file(raw_dir, "*.html")
                data_file = self._latest_file(data_dir, "*.yaml")

                if not raw_file and not data_file:
                    continue

                html = None
                data = None
                timestamp = None
                params = self._params_from_key(params_key)

                if raw_file:
                    html = raw_file.read_text(encoding="utf-8")
                    timestamp = raw_file.stem

                if data_file:
                    with data_file.open("r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    timestamp = timestamp or data_file.stem

                if endpoint not in self.bag:
                    self.bag[endpoint] = {}

                self.bag[endpoint][params_key] = {
                    config.BAG_FIELD_PARAMS: params,
                    config.BAG_FIELD_URL: None,
                    config.BAG_FIELD_HTML: html,
                    config.BAG_FIELD_DATA: data,
                    config.BAG_FIELD_TIMESTAMP: timestamp,
                }


    # helpers

    def _raw_dir_endpoint(self, endpoint):
        return self.nest_root / config.NEST_PATH_RAW / endpoint
    
    def _raw_dir_params(self, endpoint, params):
         return self._raw_dir_endpoint(endpoint) / self._params_key(params)

    def _data_dir_endpoint(self, endpoint):
        return self.nest_root / config.NEST_PATH_DATA / endpoint
    
    def _data_dir_params(self, endpoint, params):
        return self._data_dir_endpoint(endpoint) / self._params_key(params)

    def _params_key(self, params):
        if not params:
            return "_"

        parts = []
        for key in sorted(params):
            value = str(params[key])
            safe_key = self._safe_path_part(key)
            safe_value = self._safe_path_part(value)
            parts.append(f"{safe_key}={safe_value}")

        return "__".join(parts)

    def _params_from_key(self, params_key):
        if not params_key or params_key == "_":
            return {}

        params = {}

        for part in params_key.split("__"):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            params[key] = value

        return params

    def _safe_path_part(self, value):
        forbidden = '<>:"/\\|?*'
        result = str(value)

        for char in forbidden:
            result = result.replace(char, "_")

        return result.strip() or "_"

    def _latest_file(self, directory: Path, pattern: str):
        if not directory.exists():
            return None

        files = [p for p in directory.glob(pattern) if p.is_file()]
        if not files:
            return None

        return max(files, key=lambda p: p.stem)

    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")