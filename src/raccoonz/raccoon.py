import config
import constants
from bin import load as load_bin
from .errors import EndpointNotFoundError, BinKeyError
from .fetcher.factory import build_fetcher


class Raccoon:

    def __init__(self, bin: str, debug: bool=False, **kwargs):
        self.bin = bin
        self.config = load_bin(bin)
        self.debug = debug

        default_fetcher = config.DEFAULT_FETCHER
        default_parser = config.DEFAULT_PARSER

        bin_fetcher = self.config.get(constants.BIN_KEY_FETCHER, default_fetcher)
        bin_parser = self.config.get(constants.BIN_KEY_PARSER, default_parser)

        self.fetcher = build_fetcher(bin_fetcher, **kwargs)


    def dig(self, endpoint, params, refresh=False):

        endpoints = self.config.get("endpoints", {})

        if endpoint not in endpoints:
            raise EndpointNotFoundError(endpoint)
        
        ep = endpoints[endpoint]

        base_url = self.config.get(constants.BIN_KEY_URL)
        path = ep.get(constants.BIN_KEY_ENDPOINT_PATH)

        if not base_url:
            raise BinKeyError(bin, constants.BIN_KEY_URL)
        
        if not path:
            raise BinKeyError(bin, constants.BIN_KEY_ENDPOINT_PATH)
        
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}".format(**params)

        data = self.fetcher.fetch(url)

        print(data)