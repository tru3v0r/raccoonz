from .base import BaseFetcher
from playwright.sync_api import sync_playwright
from ...constants import config


class PlaywrightFetcher(BaseFetcher):

    def __init__(self, headless=config.PLAYWRIGHT_HEADLESS, timeout=config.PLAYWRIGHT_TIMEOUT):
        self.headless = headless
        self.timeout = timeout
    
    def fetch(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=config.PLAYWRIGHT_CONTEXT_USER_AGENT,
                locale=config.PLAYWRIGHT_CONTEXT_LOCALE,
                extra_http_headers=config.PLAYWRIGHT_EXTRA_HTTP_HEADERS,
            )
            page = context.new_page()
            page.goto(url, timeout=self.timeout, wait_until=config.PLAYWRIGHT_PAGE_WAIT_UNTIL)
            page.wait_for_timeout(config.PLAYWRIGHT_PAGE_TIMEOUT)
            html = page.content()

            browser.close()

        return html