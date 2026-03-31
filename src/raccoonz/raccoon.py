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

        data = self.fetcher.fetch(url)

        result = self.parser.parse(
            data,
            ep.get(bin_keys.FIELDS))
        
        return result