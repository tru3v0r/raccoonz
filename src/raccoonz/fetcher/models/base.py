from abc import ABC, abstractmethod


class BaseFetcher(ABC):

    @abstractmethod
    def fetch(self, url, fields, wait_selector, fetch_conf, lang):
        pass