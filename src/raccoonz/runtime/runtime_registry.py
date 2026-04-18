from ..fetcher.factory import build_fetcher
from ..parser.factory import build_parser


class RuntimeRegistry:
    def __init__(self):
        self._fetchers = {}
        self._parsers = {}

    def get_fetcher(self, bin_data):
        name = bin_data.fetcher

        if name not in self._fetchers:
            self._fetchers[name] = build_fetcher(name)

        return self._fetchers[name]

    def get_parser(self, bin_data):
        name = bin_data.parser

        if name not in self._parsers:
            self._parsers[name] = build_parser(name, config=bin_data.raw)

        return self._parsers[name]

    def get_runtime(self, bin_data):
        return (
            self.get_fetcher(bin_data),
            self.get_parser(bin_data),
        )