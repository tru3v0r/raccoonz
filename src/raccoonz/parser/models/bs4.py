from .base import BaseParser
from bs4 import BeautifulSoup
import raccoonz.constants.bin_keys as bin_keys
from raccoonz.errors import SelectorSyntaxError



class BS4Parser(BaseParser):

    def parse(self, html, fields, careless=False):
        soup = BeautifulSoup(html, "html.parser")
        result = {}
        errors = []

        for key, value in fields.items():
            answer = None

            elements = self._select(soup, key, value, errors)

            if elements:
                extracted = self._extract(elements, value)
                filtered = self._filter(extracted, value)
                answer = self._type(filtered, value)

            if answer is None:
                errors.append(f"Missing field: {key}")

            result[key] = answer

        result["_errors"] = errors
        return result
    

    def _select(self, soup, key, value, errors):
        selectors = value.get(bin_keys.FIELD_SELECT, {}).get(bin_keys.FIELD_SELECT_CSS, [])

        for selector in selectors:
            print(f"selector: {selector}")

            if not selector:
                errors.append(f"Empty selector for field: {key}")
                continue

            try:
                elements = soup.select(selector)
            except Exception:
                errors.append(f"Invalid selector for field '{key}': {selector}")
                continue

            if elements:
                return elements

        return None


    def _extract(self, elements, value):
        pass

    def _filter(self, values, value):
        pass

    def _type(self, values, value):
        pass