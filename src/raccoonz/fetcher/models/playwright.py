from .base import BaseFetcher
from playwright.sync_api import sync_playwright
from ...constants import config, bin_keys



class PlaywrightFetcher(BaseFetcher):

    def __init__(self, headless=config.PLAYWRIGHT_HEADLESS, timeout=config.PLAYWRIGHT_TIMEOUT):
        self.headless = headless
        self.timeout = timeout
    


    def fetch(
            self,
            url,
            wait_selector,
            fetch_conf=None,
            lang=config.PLAYWRIGHT_CONTEXT_LOCALE
    ):
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=config.PLAYWRIGHT_CONTEXT_USER_AGENT,
                locale=lang,
                extra_http_headers= {
                    **config.PLAYWRIGHT_EXTRA_HTTP_HEADERS,
                    "Accept-Language": lang
                }
            )
            page = context.new_page()
            page.goto(url, timeout=self.timeout, wait_until=config.PLAYWRIGHT_PAGE_WAIT_UNTIL)
            
            if wait_selector:
                page.wait_for_selector(wait_selector, state="attached", timeout=self.timeout)

            else:
                page.wait_for_timeout(config.PLAYWRIGHT_PAGE_TIMEOUT)
            
            if fetch_conf:
                wait_ms = fetch_conf.get(bin_keys.FETCH_WAIT_MS, 1000)

                scroll_conf = fetch_conf.get(bin_keys.FETCH_SCROLL_TO)
                if scroll_conf:
                    selector = scroll_conf.get(bin_keys.FIELD_SELECT, {}).get(bin_keys.FIELD_SELECT_CSS)

                    if selector:
                        loc = page.locator(selector)
                        if loc.count() > 0:
                            loc.first.scroll_into_view_if_needed()
                            page.wait_for_timeout(wait_ms)

            html = page.content()

            browser.close()

        return html