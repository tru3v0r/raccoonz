from .base import BaseFetcher
import requests
from ...errors import FetchingError



class RequestsFetcher(BaseFetcher):


    def __init__(self, timeout=10, headers=None):
        self.timeout = timeout
        self.headers = headers or {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        }


    def fetch(self, url):
        response = requests.get(url, timeout=self.timeout, headers=self.headers)

        if response.status_code != 200:
            raise FetchingError(url=url, detail=f"HTTP response code is {response.status_code}")
        
        if not response.content:
            raise FetchingError(url=url, detail="HTTP response is empty")
        
        return response.text