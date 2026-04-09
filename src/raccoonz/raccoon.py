from pathlib import Path
from datetime import datetime
import yaml
import hashlib
import re

from .constants import config
from .constants import bin_keys
from .errors import BinNotFoundError, URLKeyError, EndpointNotFoundError, BinKeyError
from .fetcher.factory import build_fetcher
from .parser.factory import build_parser
from .record import Record


class Raccoon:


    def __init__(
            self,
            packing_mode=config.PACKING_MODE_LAZY, 
            debug: bool=False,
    ):

        self.bins = {}
        self.fetchers = {}
        self.parsers = {}
        self.bag = {}
        self.nest_root = Path(config.NEST_PATH)
        self.fully_packed = False

        self.debug = debug

        self.packing_mode = packing_mode
        if packing_mode == config.PACKING_MODE_EAGER:
            self._pack()



    def _load_bin(self, bin) ->dict:
        bin_path = Path(config.BINS_PATH) / f"{bin}.yaml"

        if not bin_path.exists():
            raise BinNotFoundError(bin=bin)
        
        content = bin_path.read_text(encoding=config.FILE_ENCODING_UTF8)
        data = yaml.safe_load(content) or {}

        hash = hashlib.sha256(content.encode()).hexdigest()

        return { config.BIN_CONFIG: data, config.BIN_HASH: hash }
        


    def dig(
            self, 
            bin: str,
            endpoint: str, 
            *,
            refresh=False, 
            result_type=config.RESULT_TYPE_DICT,
            lang=config.PLAYWRIGHT_CONTEXT_LOCALE,
            **params
    ):
        
        bin_data = self._load_bin(bin)
        self.bins[bin] = bin_data

        default_fetcher = config.DEFAULT_FETCHER
        default_parser = config.DEFAULT_PARSER

        bin_config = bin_data[config.BIN_CONFIG]

        bin_fetcher = bin_config.get(bin_keys.FETCHER, default_fetcher)
        if bin_fetcher not in self.fetchers:
            self.fetchers[bin_fetcher] = build_fetcher(bin_fetcher)

        bin_parser = bin_config.get(bin_keys.PARSER, default_parser)
        if bin_parser not in self.parsers:
            self.parsers[bin_parser] = build_parser(bin_parser, config=bin_config)

        endpoints = bin_config.get(bin_keys.ENDPOINTS, {})

        if endpoint not in endpoints:
            raise EndpointNotFoundError(endpoint)
        
        ep = endpoints[endpoint]

        base_url = bin_config.get(bin_keys.URL)
        path = ep.get(bin_keys.ENDPOINT_PATH)

        if not base_url:
            raise BinKeyError(bin, bin_keys.URL)
        
        if not path:
            raise BinKeyError(bin, bin_keys.ENDPOINT_PATH)
        
        try:
            url = f"{base_url.rstrip('/')}/{path.lstrip('/')}".format(**params)
        except KeyError as e:
            missing = e.args[0]
            expected = [p.strip("{}") for p in path.split("/") if "{" in p]
            raise URLKeyError(
                missing,
                endpoint,
                expected=expected,
                got=list(params.keys())
            )
        
        params_key = self._record_key(params, lang)

        if self.packing_mode == config.PACKING_MODE_LAZY and not refresh:
            self._pack_one(bin, endpoint, lang=lang, **params)
        
        cached = self.bag[bin].get(endpoint, {}).get(params_key)
        if not refresh and cached and cached.data is not None:
            return cached.data
        
        wait_selector = bin_config.get(bin_keys.ENDPOINT_WAIT_SELECTOR)
        
        fetch_conf = bin_config.get(bin_keys.FETCH)

        html = self.fetchers[bin_fetcher].fetch(
            url,
            wait_selector=wait_selector,
            fetch_conf=fetch_conf,
            lang=lang
        )

        result = self.parsers[bin_parser].parse(
            html,
            ep.get(bin_keys.FIELDS))
        
        timestamp = self._timestamp()

        record = Record(
            params,
            url,
            html,
            result,
            timestamp,
            lang=lang
        )

        self._stash(bin, endpoint, record)
        self._hoard(bin, endpoint, record)
        
        # return object
        if result_type == config.RESULT_TYPE_OBJECT:
            from .object import Object
            result = Object(result)

        return result
    


    def serve(
            self,
            bin: str,
            bins: list,
            port=8000
    ):
        pass



    # load everything from nest to bag (eager)
    def _pack(self):
        if not self.nest_root.exists():
            return

        for bin_dir in self.nest_root.iterdir():
            if not bin_dir.is_dir():
                continue

            bin = bin_dir.name

            for lang_dir in self.nest_root.iterdir():
                if not lang_dir.is_dir():
                    continue

                lang = lang_dir.name

                for endpoint_dir in lang_dir.iterdir():
                    if not endpoint_dir.is_dir():
                        continue

                    endpoint = endpoint_dir.name
                    data_dir = endpoint_dir / config.NEST_PATH_DATA
                    raw_dir = endpoint_dir / config.NEST_PATH_RAW

                    if not data_dir.exists():
                        continue

                    #file with the last alphabetical name
                    data_file = sorted(data_dir.glob("*.yaml"))[-1]

                    with data_file.open("r", encoding=config.FILE_ENCODING_UTF8) as f:
                        payload = yaml.safe_load(f) or {}

                    meta = payload.get(config.NEST_FIELD_META, {})
                    data = payload.get(config.NEST_FIELD_DATA)

                    params = meta.get(config.NEST_FIELD_PARAMS, {})
                    timestamp = meta.get(config.NEST_FIELD_TIMESTAMP) or data_file.stem.rsplit("_", 1)[-1]
                    url = meta.get(config.NEST_FIELD_URL)
                    file_lang = meta.get(config.NEST_FIELD_LANG, lang)

                    params_key = self._params_key(params)
                    raw_file = raw_dir / f"{params_key}_{timestamp}.html"
                    html = raw_file.read_text(encoding=config.FILE_ENCODING_UTF8) if raw_file.exists() else None

                    record = Record(
                        params=params,
                        url=url,
                        html=html,
                        data=data,
                        timestamp=timestamp,
                        lang=file_lang,
                    )

                    if endpoint not in self.bag:
                        self.bag[bin][endpoint] = {}

                    self.bag[bin][endpoint][self._record_key(params, file_lang)] = record

        self.fully_packed = True


    # load latest endpoint from nest to bag (lazy)
    def _pack_one(self, bin, endpoint, *, lang, **params):
        record_key = self._record_key(params, lang)

        if bin in self.bag and endpoint in self.bag[bin] and record_key in self.bag[bin][endpoint]:
            return

        raw_dir = self._raw_dir_endpoint(bin, lang, endpoint)
        data_dir = self._data_dir_endpoint(bin, lang, endpoint)

        params_key = self._params_key(params)
        pattern = f"{params_key}_*.yaml"

        if not data_dir.exists():
            return

        data_files = [p for p in data_dir.glob(pattern) if p.is_file()]
        if not data_files:
            return

        data_file = max(data_files, key=lambda p: p.stem.rsplit("_", 1)[-1])

        with data_file.open("r", encoding=config.FILE_ENCODING_UTF8) as f:
            payload = yaml.safe_load(f) or {}

        meta = payload.get(config.NEST_FIELD_META, {})
        data = payload.get(config.NEST_FIELD_DATA)
        timestamp = meta.get(config.NEST_FIELD_TIMESTAMP) or data_file.stem.rsplit("_", 1)[-1]
        url = meta.get(config.NEST_FIELD_URL)
        file_params = meta.get(config.NEST_FIELD_PARAMS, params)
        file_lang = meta.get(config.NEST_FIELD_LANG, lang)

        raw_file = raw_dir / f"{params_key}_{timestamp}.html"
        html = raw_file.read_text(encoding=config.FILE_ENCODING_UTF8) if raw_file.exists() else None

        record = Record(
            params=file_params,
            url=url,
            html=html,
            data=data,
            timestamp=timestamp,
            lang=file_lang,
        )

        if bin not in self.bag:
            self.bag[bin] = {}

        if endpoint not in self.bag[bin]:
            self.bag[bin][endpoint] = {}

        self.bag[bin][endpoint][record_key] = record



    # write to bag
    def _stash(self, bin, endpoint, record):
        record_key = self._record_key(record.params, record.lang)

        if bin not in self.bag or endpoint not in self.bag[bin]:
            self.bag[endpoint] = {}

        self.bag[bin][endpoint][record_key] = record



    # write to nest
    def _hoard(self, bin, endpoint, record):
        raw_dir = self._raw_dir_endpoint(bin, record.lang, endpoint)
        data_dir = self._data_dir_endpoint(bin, record.lang, endpoint)

        raw_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        stem = self._record_stem(record.params, record.timestamp)

        raw_path = raw_dir / f"{stem}.html"
        data_path = data_dir / f"{stem}.yaml"

        if record.html is not None:
            raw_path.write_text(record.html, encoding=config.FILE_ENCODING_UTF8)

        payload = {
            config.NEST_FIELD_META: {
                config.NEST_FIELD_BIN: bin,
                config.NEST_FIELD_VERSION: self.bins[bin][config.BIN_CONFIG].get(config.NEST_FIELD_VERSION),
                config.NEST_FIELD_HASH: self._bin_hash(bin),
                config.NEST_FIELD_ENDPOINT: endpoint,
                config.NEST_FIELD_LANG: record.lang,
                config.NEST_FIELD_PARAMS: record.params,
                config.NEST_FIELD_TIMESTAMP: record.timestamp,
                config.NEST_FIELD_URL: record.url,
            },
            config.NEST_FIELD_DATA: record.data,
        }

        with data_path.open("w", encoding=config.FILE_ENCODING_UTF8) as f:
            yaml.safe_dump(payload, f, allow_unicode=True, sort_keys=False)



    # helpers

    def _bin_dir(self, bin):
        return self.nest_root / bin



    def _lang_dir(self, bin, lang):
        return self._bin_dir(bin) / self._safe_path_part(lang)



    def _endpoint_dir(self, bin, lang, endpoint):
        return self._lang_dir(bin, lang) / endpoint



    def _raw_dir_endpoint(self, bin, lang, endpoint):
        return self._endpoint_dir(bin, lang, endpoint) / config.NEST_PATH_RAW



    def _data_dir_endpoint(self, bin, lang, endpoint):
        return self._endpoint_dir(bin, lang, endpoint) / config.NEST_PATH_DATA



    def _record_key(self, params, lang):
        return f"{self._safe_path_part(lang)}::{self._params_key(params)}"



    def _params_key(self, params):
        if not params:
            return "_"

        parts = []
        for key in sorted(params):
            safe_key = self._safe_path_part(key)
            safe_value = self._safe_path_part(params[key])
            parts.append(f"{safe_key}={safe_value}")

        return ",".join(parts)



    def _record_stem(self, params, timestamp):
        return f"{self._params_key(params)}_{timestamp}"



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



    def _bin_hash(self, bin):
        return self.bins[bin][config.BIN_HASH]



    def _timestamp(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")