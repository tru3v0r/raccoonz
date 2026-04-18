from pathlib import Path

from .constants import config
from .constants import bin_keys
from .config.bin_loader import BinLoader
from .storage.filesystem import FileSystemStorage
from .storage.bag import Bag
from .sniff.sniffer import Sniffer
from .serve.server import Server
from .errors import URLKeyError, EndpointNotFoundError, BinKeyError
from .runtime.runtime_registry import RuntimeRegistry
from .record import Record
from .utils.time import now_timestamp


class Raccoon:


    def __init__(
            self,
            packing_mode=config.PACKING_MODE_LAZY, 
            debug: bool=False,
    ):

        self.bins = {}
        self.bin_loader = BinLoader()
        self.runtime = RuntimeRegistry()
        self.sniffer = Sniffer(
            load_bin=self.bin_loader.load,
            list_bins=self.bin_loader.list,
            dig=self.dig,
        )
        self.bag = Bag()
        self.nest_root = Path(config.NEST_PATH)
        self.storage = FileSystemStorage(self.nest_root)
        self.server = Server(
            pack=self.storage.pack,
            find_records=self.bag.find,
            bag=self.bag,
        )
        self.debug = debug
        self.fully_packed = False

        self.packing_mode = packing_mode
        if packing_mode == config.PACKING_MODE_EAGER:
            self.storage.pack(self.bag.content)
            self.fully_packed = True
        

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
        bin_data = self._load_bin_data(bin)
        fetcher, parser = self.runtime.get_runtime(bin_data)
        endpoint_data = self._get_endpoint(bin_data, endpoint)
        url = self._build_url(bin, bin_data, endpoint_data, endpoint, params)

        cached = self._load_cached_record(
            bin,
            endpoint,
            lang=lang,
            refresh=refresh,
            params=params,
        )
        if cached is not None:
            result = cached.data
        else:
            html = self._fetch_html(fetcher, url, bin_data, lang)
            result = self._parse_result(parser, html, endpoint_data)
            record = self._build_record(params, url, html, result, lang=lang)
            self._persist_record(bin, endpoint, bin_data, record)

        if result_type == config.RESULT_TYPE_OBJECT:
            from .object import Object
            return Object(result)

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



    def _reload_one(self, bin, endpoint, *, lang, **params):
        self.bag.delete_endpoint(bin, endpoint)
        self.storage.pack_one(self.bag.content, bin, endpoint, lang=lang, **params)


    def _load_bin_data(self, bin_name):
        bin_data = self.bin_loader.load(bin_name)
        self.bins[bin_name] = bin_data
        return bin_data


    def _get_endpoint(self, bin_data, endpoint_name):
        endpoint = bin_data.get_endpoint(endpoint_name)
        if endpoint is None:
            raise EndpointNotFoundError(endpoint_name)
        return endpoint


    def _build_url(self, bin_name, bin_data, endpoint, endpoint_name, params):
        base_url = bin_data.url
        path = endpoint.path

        if not base_url:
            raise BinKeyError(bin_name, bin_keys.URL)

        if not path:
            raise BinKeyError(bin_name, bin_keys.ENDPOINT_PATH)

        try:
            return f"{base_url.rstrip('/')}/{path.lstrip('/')}".format(**params)
        except KeyError as e:
            missing = e.args[0]
            expected = [p.strip("{}") for p in path.split("/") if "{" in p]
            raise URLKeyError(
                missing,
                endpoint_name,
                expected=expected,
                got=list(params.keys())
            )


    def _load_cached_record(self, bin_name, endpoint_name, *, lang, refresh, params):
        if self.packing_mode == config.PACKING_MODE_LAZY and not refresh:
            self.storage.pack_one(self.bag.content, bin_name, endpoint_name, lang=lang, **params)

        cached = self.bag.get(bin_name, endpoint_name, params=params, lang=lang)

        if not refresh and cached and cached.data is not None:
            return cached

        return None


    def _fetch_html(self, fetcher, url, bin_data, lang):
        return fetcher.fetch(
            url,
            wait_selector=bin_data.raw.get(bin_keys.ENDPOINT_WAIT_SELECTOR),
            fetch_conf=bin_data.fetch,
            lang=lang,
        )


    def _parse_result(self, parser, html, endpoint):
        return parser.parse(html, endpoint.fields)



    def _build_record(self, params, url, html, result, *, lang):
        return Record(
            params,
            url,
            html,
            result,
            now_timestamp(),
            lang=lang,
        )


    def _persist_record(self, bin_name, endpoint_name, bin_data, record):
        self.bag.stash(bin_name, endpoint_name, record)
        self.storage.hoard(
            bin_name,
            endpoint_name,
            record,
            bin_version=bin_data.version,
            bin_hash=bin_data.hash,
        )