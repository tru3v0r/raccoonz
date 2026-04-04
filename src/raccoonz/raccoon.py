from pathlib import Path
from datetime import datetime
import yaml

from .constants import config
from .constants import bin_keys
from .bin import load as load_bin
from .errors import EndpointNotFoundError, BinKeyError
from .fetcher.factory import build_fetcher
from .parser.factory import build_parser
from .record import Record


class Raccoon:


    def __init__(
            self,
            bin: str,
            packing_mode=config.PACKING_MODE_LAZY, 
            debug: bool=False,
            **kwargs
    ):
        self.bin = bin
        self.config = load_bin(bin)
        self.packing_mode = packing_mode
        self.debug = debug

        default_fetcher = config.DEFAULT_FETCHER
        default_parser = config.DEFAULT_PARSER

        bin_fetcher = self.config.get(bin_keys.FETCHER, default_fetcher)
        bin_parser = self.config.get(bin_keys.PARSER, default_parser)

        self.fetcher = build_fetcher(bin_fetcher, **kwargs)
        self.parser = build_parser(bin_parser, config=self.config, **kwargs)

        self.bag = {}
        self.nest_root = Path(config.NEST_PATH) / self.bin

        # eager packing mode
        if packing_mode == config.PACKING_MODE_EAGER:
            self._pack()


    def dig(
            self, 
            endpoint, 
            params, 
            refresh=False, 
            result_type=config.RESULT_TYPE_DICT
    ):

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

        # lazy packing mode
        if self.packing_mode == config.PACKING_MODE_LAZY:
            self._pack_one(endpoint, params)
        
        cached = self.bag.get(endpoint, {}).get(params_key)
        if not refresh and cached and cached.data is not None:
            print("Returning cached data")
            return cached.data
        
        wait_selector = self.config.get(bin_keys.ENDPOINT_WAIT_SELECTOR)
        
        html = self.fetcher.fetch(url, wait_selector=wait_selector)

        result = self.parser.parse(
            html,
            ep.get(bin_keys.FIELDS))
        
        timestamp = self._timestamp()

        record = Record(params, url, html, result, timestamp)

        self._stash(endpoint, record)
        self._hoard(endpoint, record)
        
        # return object
        if result_type == config.RESULT_TYPE_OBJECT:
            from .object import Object
            result = Object(result)

        return result
    


    # load everything from nest to bag (eager)
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

                raw_file = self._latest_file(raw_dir, "*.html") if raw_dir.exists() else None
                data_file = self._latest_file(data_dir, "*.yaml") if data_dir.exists() else None

                if not raw_file and not data_file:
                    continue

                html = None
                data = None
                timestamp = None
                url = None
                params = self._params_from_key(params_key)

                if raw_file:
                    html = raw_file.read_text(encoding=config.FILE_ENCODING_UTF8)
                    timestamp = raw_file.stem

                if data_file:
                    with data_file.open("r", encoding=config.FILE_ENCODING_UTF8) as f:
                        payload = yaml.safe_load(f) or {}

                    meta = payload.get(config.NEST_FIELD_META, {})
                    data = payload.get(config.NEST_FIELD_DATA)
                    params = meta.get(config.NEST_FIELD_PARAMS, params)
                    url = meta.get(config.NEST_FIELD_URL)
                    timestamp = meta.get(config.NEST_FIELD_TIMESTAMP) or timestamp or data_file.stem

                record = Record(
                    params=params,
                    url=url,
                    html=html,
                    data=data,
                    timestamp=timestamp,
                )

                if endpoint not in self.bag:
                    self.bag[endpoint] = {}

                self.bag[endpoint][params_key] = record


    # load latest endpoint from nest to bag (lazy)
    def _pack_one(self, endpoint, params):
        params_key = self._params_key(params)

        if endpoint in self.bag and params_key in self.bag[endpoint]:
            return

        raw_dir = self._raw_dir_endpoint(endpoint) / params_key
        data_dir = self._data_dir_endpoint(endpoint) / params_key

        raw_file = self._latest_file(raw_dir, "*.html") if raw_dir.exists() else None
        data_file = self._latest_file(data_dir, "*.yaml") if data_dir.exists() else None

        if not raw_file and not data_file:
            return

        html = None
        data = None
        timestamp = None
        url = None

        if raw_file:
            html = raw_file.read_text(encoding=config.FILE_ENCODING_UTF8)
            timestamp = raw_file.stem

        if data_file:
            with data_file.open("r", encoding=config.FILE_ENCODING_UTF8) as f:
                payload = yaml.safe_load(f) or {}

            meta = payload.get("meta", {})
            data = payload.get("data")
            params = meta.get("params", params)
            url = meta.get("url")
            timestamp = meta.get("timestamp") or timestamp or data_file.stem

        record = Record(
            params=params,
            url=url,
            html=html,
            data=data,
            timestamp=timestamp,
        )

        if endpoint not in self.bag:
            self.bag[endpoint] = {}

        self.bag[endpoint][params_key] = record


    # write to bag
    def _stash(self, endpoint, record):
        params_key = self._params_key(record.params)

        if endpoint not in self.bag:
            self.bag[endpoint] = {}

        self.bag[endpoint][params_key] = record


    # write to nest
    def _hoard(self, endpoint, record):
        raw_dir = self._raw_dir_params(endpoint, record.params)
        data_dir = self._data_dir_params(endpoint, record.params)

        raw_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        raw_path = raw_dir / f"{record.timestamp}.html"
        data_path = data_dir / f"{record.timestamp}.yaml"

        if record.html is not None:
            raw_path.write_text(record.html, encoding=config.FILE_ENCODING_UTF8)

        payload = {
            config.NEST_FIELD_META: {
                config.NEST_FIELD_BIN: self.bin,
                config.NEST_FIELD_VERSION: self.config.get(config.NEST_FIELD_VERSION),
                config.NEST_FIELD_HASH: self.config.get(config.NEST_FIELD_HASH),
                config.NEST_FIELD_ENDPOINT: endpoint,
                config.NEST_FIELD_PARAMS: record.params,
                config.NEST_FIELD_TIMESTAMP: record.timestamp,
                config.NEST_FIELD_URL: record.url,
            },
            config.NEST_FIELD_DATA: record.data,
        }

        with data_path.open("w", encoding=config.FILE_ENCODING_UTF8) as f:
            yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)


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