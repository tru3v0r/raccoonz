from .base import BaseFetcher
import requests
from ...constants import config
from ...errors import FetchingError



class RequestsFetcher(BaseFetcher):


    def __init__(self, timeout=config.REQUESTS_TIMEOUT, headers=None):
        self.timeout = timeout
        self.headers = headers or {
            "User-Agent": config.REQUESTS_HEADERS_USER_AGENT,
            "Accept": config.REQUESTS_HEADERS_ACCEPT,
            "Accept-Language": config.REQUESTS_HEADERS_ACCEPT_LANGUAGE,
            "Accept-Encoding": config.REQUESTS_HEADERS_ACCEPT_ENCODING,
            "Connection": config.REQUESTS_HEADERS_CONNECTION,
            "Upgrade-Insecure-Requests": config.REQUESTS_HEADERS_UPGRADE_INSECURE_REQUESTS,
            "Referer": config.REQUESTS_HEADERS_REFERER,
            "DNT": config.REQUESTS_HEADERS_DNT
        }


    def fetch(self, url):
        response = requests.get(url, timeout=self.timeout, headers=self.headers)

        if response.status_code != 200:
            raise FetchingError(url=url, detail=f"HTTP response code is {response.status_code}")
        
        if not response.content:
            raise FetchingError(url=url, detail="HTTP response is empty")
        
        return response.text