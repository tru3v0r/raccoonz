from .base import BaseFetcher
from playwright.sync_api import sync_playwright


class PlaywrightFetcher(BaseFetcher):

    def __init__(self, headless=True, timeout=10000):
        self.headless = headless
        self.timeout = timeout
    
    def fetch(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10/0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
            page = context.new_page()
            page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            html = page.content()

            browser.close()

        return html