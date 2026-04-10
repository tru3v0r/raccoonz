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
        
        cached = self.bag.get(bin, {}).get(endpoint, {}).get(params_key)
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

            for endpoint_name, ep in endpoints.items():
                path = ep.get(bin_keys.ENDPOINT_PATH)
                if not path:
                    continue

                regex, keys = self._path_to_regex(path)

                m = re.match(regex, url_path)
                if not m:
                    continue

                params = dict(zip(keys, m.groups()))

                match = {
                    "bin": bin_name,
                    "endpoint": endpoint_name,
                    "params": params,
                }

                if dig:
                    match = self.dig(
                        bin_name,
                        endpoint_name,
                        refresh=False,
                        lang=lang,
                        **params
                    )

                matches.append(match)

        return matches or None



    def serve(
            self,
            bin: str=None,
            bins: list=None,
            endpoint: str=None,
            endpoints: list=None,
            lang: str=None,
            port=config.SERVE_DEFAULT_PORT
    ):
        from fastapi import FastAPI, HTTPException, Request
        import uvicorn

        self._pack()

        app = FastAPI()

        bin_filter = self._merge_filters(bin, bins)
        endpoint_filter = self._merge_filters(endpoint, endpoints)

        @app.get("/")
        def serve_root(request: Request):
            query_params = dict(request.query_params)

            effective_lang = self._resolve_served_lang(
                requested_lang=query_params.get("lang"),
                served_lang=lang,
                bin_filter=bin_filter,
                endpoint_filter=endpoint_filter,
                query_params=query_params
            )

            records = self._served_records(
                bin_filter=bin_filter,
                endpoint_filter=endpoint_filter,
                lang=effective_lang,
                query_params=self._clean_query_params(query_params)
            )

            if not records:
                raise HTTPException(status_code=404, detail="No matching records")

            return self._format_records_response(records)

        @app.get("/{path:path}")
        def serve_path(path: str, request: Request):
            parts = [p for p in path.split("/") if p]
            query_params = dict(request.query_params)

            path_bin = parts[0] if len(parts) >= 1 else None
            path_endpoint = parts[1] if len(parts) >= 2 else None

            current_bin_filter = {path_bin} if path_bin else bin_filter
            current_endpoint_filter = {path_endpoint} if path_endpoint else endpoint_filter

            if path_bin and bin_filter is not None and path_bin not in bin_filter:
                raise HTTPException(status_code=404, detail="Bin not served")

            if path_endpoint and endpoint_filter is not None and path_endpoint not in endpoint_filter:
                raise HTTPException(status_code=404, detail="Endpoint not served")

            effective_lang = self._resolve_served_lang(
                requested_lang=query_params.get("lang"),
                served_lang=lang,
                bin_filter=current_bin_filter,
                endpoint_filter=current_endpoint_filter,
                query_params=query_params
            )

            records = self._served_records(
                bin_filter=current_bin_filter,
                endpoint_filter=current_endpoint_filter,
                lang=effective_lang,
                query_params=self._clean_query_params(query_params)
            )

            if not records:
                raise HTTPException(status_code=404, detail="No matching records")

            if len(parts) <= 2:
                return self._format_records_response(records)

            field_path = parts[2:]
            resolved = []

            for item in records:
                try:
                    value = self._resolve_path(item["record"].data, field_path)
                except (KeyError, IndexError, TypeError):
                    continue

                resolved.append({
                    "bin": item["bin"],
                    "endpoint": item["endpoint"],
                    "lang": item["record"].lang,
                    "params": item["record"].params,
                    "timestamp": item["record"].timestamp,
                    "value": value,
                })

            if not resolved:
                raise HTTPException(status_code=404, detail="Field not found")

            if len(resolved) == 1:
                return resolved[0]["value"]

            return resolved

        uvicorn.run(app, host="127.0.0.1", port=port)


    # send a signal to reload endpoint
    def nudge(self, bin: str, endpoint: str, *, lang: str, **params):
        self._reload_one(bin, endpoint, lang=lang, **params)



    # load everything from nest to bag (eager)
    def _pack(self):

        self.bag = {}

        if not self.nest_root.exists():
            return

        for bin_dir in self.nest_root.iterdir():
            if not bin_dir.is_dir():
                continue

            bin = bin_dir.name

            for lang_dir in bin_dir.iterdir():
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

                    for data_file in data_dir.glob("*.yaml"):
                        if data_file.parent.name == "_expired":
                            continue

                        with data_file.open("r", encoding=config.FILE_ENCODING_UTF8) as f:
                            payload = yaml.safe_load(f) or {}

                        meta = payload.get(config.NEST_FIELD_META, {})
                        data = payload.get(config.NEST_FIELD_DATA)

                        params = meta.get(config.NEST_FIELD_PARAMS, {})
                        timestamp = meta.get(config.NEST_FIELD_TIMESTAMP)
                        url = meta.get(config.NEST_FIELD_URL)
                        file_lang = meta.get(config.NEST_FIELD_LANG, lang)

                        params_key = self._params_key(params)
                        raw_file = raw_dir / f"{params_key}.html"
                        html = raw_file.read_text(encoding=config.FILE_ENCODING_UTF8) if raw_file.exists() else None

                        record = Record(
                            params=params,
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
        pattern = f"{params_key}.yaml"

        if not data_dir.exists():
            return

        data_files = [p for p in data_dir.glob(pattern) if p.is_file()]
        if not data_files:
            return

        data_file = data_files[0]
        with data_file.open("r", encoding=config.FILE_ENCODING_UTF8) as f:
            payload = yaml.safe_load(f) or {}

        meta = payload.get(config.NEST_FIELD_META, {})
        data = payload.get(config.NEST_FIELD_DATA)
        timestamp = meta.get(config.NEST_FIELD_TIMESTAMP)
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

        if bin not in self.bag:
            self.bag[bin] = {}
            
        if endpoint not in self.bag[bin]:
            self.bag[bin][endpoint] = {}

        self.bag[bin][endpoint][record_key] = record



    # write to nest
    def _hoard(self, bin, endpoint, record):
        raw_dir = self._raw_dir_endpoint(bin, record.lang, endpoint)
        data_dir = self._data_dir_endpoint(bin, record.lang, endpoint)

        raw_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        stem = self._params_key(record.params)

        raw_path = raw_dir / f"{stem}.html"
        data_path = data_dir / f"{stem}.yaml"

        expired_dir = data_dir / config.NEST_PATH_EXPIRED
        expired_dir.mkdir(exist_ok=True)

        if data_path.exists():
            old = data_dir / f"{stem}.yaml"
            old.rename(expired_dir / f"{stem}_{self._timestamp()}.yaml")

        if raw_path.exists():
            old = raw_dir / f"{stem}.html"
            old.rename(raw_dir / config.NEST_PATH_EXPIRED / f"{stem}_{self._timestamp()}.html")

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



    def _record_stem(self, params):
        return f"{self._params_key(params)}"



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
    


    # sniff helpers

    def _normalize_url_for_sniff(self, url: str):
        url = url.strip()
        url = re.sub(r"^https?://", "", url, flags=re.IGNORECASE)
        url = url.lstrip("/")
        url = url.rstrip("/")
        return url



    def _split_base_and_path(self, url: str):
        normalized = self._normalize_url_for_sniff(url)
        parts = normalized.split("/", 1)
        base = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else "/"
        return base, path
    


    def _base_matches(self, url_base: str, bin_base_url: str):
        bin_base = self._normalize_url_for_sniff(bin_base_url).split("/", 1)[0]

        if url_base == bin_base:
            return True

        if url_base.startswith("www.") and url_base[4:] == bin_base:
            return True

        if bin_base.startswith("www.") and bin_base[4:] == url_base:
            return True

        return False



    def _path_to_regex(self, path):
        keys = re.findall(r"{(.*?)}", path)
        regex = re.escape(path)

        for key in keys:
            regex = regex.replace(r"\{" + key + r"\}", r"([^/]+)")

        regex = "^" + regex.rstrip("/") + "/?$"
        
        return regex, keys



    def _list_bins(self):
        bins_path = Path(config.BINS_PATH)
        return [p.stem for p in bins_path.glob("*.yaml")]



    #serve helpers

    def _merge_filters(self, single, multiple):
        values = set()

        if single is not None:
            values.add(single)

        if multiple:
            values.update(multiple)

        return values or None



    def _clean_query_params(self, query_params):
        query_params = dict(query_params)
        query_params.pop("lang", None)
        return query_params
    


    def _served_records(self, *, bin_filter=None, endpoint_filter=None, lang=None, query_params=None):
        results = []
        query_params = query_params or {}

        for bin_name, endpoints_map in self.bag.items():
            if bin_filter is not None and bin_name not in bin_filter:
                continue

            for endpoint_name, records_map in endpoints_map.items():
                if endpoint_filter is not None and endpoint_name not in endpoint_filter:
                    continue

                for record in records_map.values():
                    if lang is not None and record.lang != lang:
                        continue

                    if not self._record_matches_query(record, query_params):
                        continue

                    results.append({
                        "bin": bin_name,
                        "endpoint": endpoint_name,
                        "record": record,
                    })

        return results
    


    def _record_matches_query(self, record, query_params):
        for key, value in query_params.items():
            if str(record.params.get(key)) != value:
                return False
        return True
    


    def _format_records_response(self, records):
        if len(records) == 1:
            record = records[0]["record"]
            return {
                "bin": records[0]["bin"],
                "endpoint": records[0]["endpoint"],
                "lang": record.lang,
                "params": record.params,
                "timestamp": record.timestamp,
                "url": record.url,
                "data": record.data,
            }

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



    def _resolve_path(self, value, parts):
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
    

    def _resolve_served_lang(self, *, requested_lang=None, served_lang=None, bin_filter=None, endpoint_filter=None, query_params=None):
        clean_query = self._clean_query_params(query_params or {})
        candidates = []

        if requested_lang:
            candidates.append(requested_lang)

        if served_lang:
            candidates.append(served_lang)

        default_lang = getattr(config, "SERVE_DEFAULT_LANG", None)
        if default_lang:
            candidates.append(default_lang)

        for candidate in candidates:
            if self._has_served_records(
                bin_filter=bin_filter,
                endpoint_filter=endpoint_filter,
                lang=candidate,
                query_params=clean_query
            ):
                return candidate

        return self._first_served_lang(
            bin_filter=bin_filter,
            endpoint_filter=endpoint_filter,
            query_params=clean_query
        )



    def _has_served_records(self, *, bin_filter=None, endpoint_filter=None, lang=None, query_params=None):
        return bool(self._served_records(
            bin_filter=bin_filter,
            endpoint_filter=endpoint_filter,
            lang=lang,
            query_params=query_params
        ))



    def _first_served_lang(self, *, bin_filter=None, endpoint_filter=None, query_params=None):
        query_params = query_params or {}

        for bin_name, endpoints_map in self.bag.items():
            if bin_filter is not None and bin_name not in bin_filter:
                continue

            for endpoint_name, records_map in endpoints_map.items():
                if endpoint_filter is not None and endpoint_name not in endpoint_filter:
                    continue

                for record in records_map.values():
                    if self._record_matches_query(record, query_params):
                        return record.lang

        return None
    

    def _reload_one(self, bin, endpoint, *, lang, **params):
        if bin in self.bag and endpoint in self.bag[bin]:
            self.bag[bin].pop(endpoint, None)
            if not self.bag[bin]:
                self.bag.pop(bin, None)

        self._pack_one(bin, endpoint, lang=lang, **params)