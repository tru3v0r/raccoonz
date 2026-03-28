from ..constants.config import DEFAULT_FETCHER
from ..errors import FetcherNotFoundError



def build_fetcher(name=DEFAULT_FETCHER, **kwargs):

    match name:

        case "playwright":
            from .models.playwright import PlaywrightFetcher
            return PlaywrightFetcher(**kwargs)
        
        case "requests":
            from .models.requests import RequestsFetcher
            return RequestsFetcher(**kwargs)
        
        case _:
            raise FetcherNotFoundError(name)