from .config import load_config
from .errors import EndpointNotFoundError, BinKeyError
from .fetcher.factory import build_fetcher


class Raccoon:

    def __init__(self, bin: str, debug: bool=False, **kwargs):
        self.bin = bin
        self.config = load_config(bin)
        self.debug = debug

        default_fetcher = "requests"
        default_parser = "bs4"

        bin_fetcher = self.config.get("fetcher", default_fetcher)
        bin_parser = self.config.get("parser", default_parser)

        self.fetcher = build_fetcher(bin_fetcher, **kwargs)

    def dig(self, endpoint, params, refresh=False):

        BASE_URL_KEY = "url"
        PATH_KEY = "path"

        endpoints = self.config.get("endpoints", {})

        if endpoint not in endpoints:
            raise EndpointNotFoundError(endpoint)
        
        ep = endpoints[endpoint]

        base_url = self.config.get(BASE_URL_KEY)
        path = ep.get(PATH_KEY)

        if not base_url:
            raise BinKeyError(bin, BASE_URL_KEY)
        
        if not path:
            raise BinKeyError(bin, PATH_KEY)
        
        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}".format(**params)

        data = self.fetcher.fetch(url)

        print(data)