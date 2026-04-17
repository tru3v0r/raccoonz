from pathlib import Path
import yaml
import hashlib
import re

from .constants import config
from .constants import bin_keys
from .storage.filesystem import FileSystemStorage
from .storage.bag import Bag
from .sniff.sniffer import Sniffer
from .serve.server import Server
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
        self.sniffer = Sniffer(
            load_bin=self._load_bin,
            list_bins=self._list_bins,
            dig=self.dig,
        )
        self.fetchers = {}
        self.parsers = {}
        self.bag = Bag()
        self.nest_root = Path(config.NEST_PATH)
        self.storage = FileSystemStorage(self.nest_root)
        self.server = Server(
            pack=self.storage.pack,
            find_records=self.bag.find,
            resolve_served_lang=self._resolve_served_lang,
            merge_filters=self._merge_filters,
            clean_query_params=self._clean_query_params,
            format_records_response=self._format_records_response,
            resolve_path=self._resolve_path,
        )
        self.debug = debug
        self.fully_packed = False

        self.packing_mode = packing_mode
        if packing_mode == config.PACKING_MODE_EAGER:
            self.storage.pack(self.bag.content)
            self.fully_packed = True



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
        
        if self.packing_mode == config.PACKING_MODE_LAZY and not refresh:
            self.storage.pack_one(self.bag.content, bin, endpoint, lang=lang, **params)
        
        cached = self.bag.get(bin, endpoint, params=params, lang=lang)
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
        
        timestamp = self.storage._timestamp()

        record = Record(
            params,
            url,
            html,
            result,
            timestamp,
            lang=lang
        )

        self.bag.stash(bin, endpoint, record)
        self.storage.hoard(
            bin,
            endpoint,
            record,
            bin_version=self.bins[bin][config.BIN_CONFIG].get(config.NEST_FIELD_VERSION),
            bin_hash=self._bin_hash(bin)
        )
        
        # return object
        if result_type == config.RESULT_TYPE_OBJECT:
            from .object import Object
            result = Object(result)

        return result
    

    def sniff(self, url: str, *, dig=False, lang=config.PLAYWRIGHT_CONTEXT_LOCALE):
        return self.sniffer.sniff(url, dig=dig, lang=lang)


    def serve(
            self,
            bin: str=None,
            bins: list=None,
            endpoint: str=None,
            endpoints: list=None,
            lang: str=None,
            port=config.SERVE_DEFAULT_PORT
    ):
        return self.server.serve(
            bag_content=self.bag.content,
            bin_name=bin,
            bin_names=bins,
            endpoint_name=endpoint,
            endpoint_names=endpoints,
            lang=lang,
            port=port,
        )

    # send a signal to reload endpoint
    def nudge(self, bin: str, endpoint: str, *, lang: str, **params):
        self._reload_one(bin, endpoint, lang=lang, **params)










    # helpers


    def _latest_file(self, directory: Path, pattern: str):
        if not directory.exists():
            return None

        files = [p for p in directory.glob(pattern) if p.is_file()]
        if not files:
            return None

        return max(files, key=lambda p: p.stem)



    def _bin_hash(self, bin):
        return self.bins[bin][config.BIN_HASH]




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
    



    



    


    def _format_records_response(self, records, *, raw=False):
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



    def _reload_one(self, bin, endpoint, *, lang, **params):
        self.bag.delete_endpoint(bin, endpoint)
        self.storage.pack_one(self.bag.content, bin, endpoint, lang=lang, **params)