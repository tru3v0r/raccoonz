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
            print(key, type(value), value)
            answer = None
            selectors = value.get(bin_keys.FIELD_SELECT, {}).get(bin_keys.FIELD_SELECT_CSS, [])

            for selector in selectors:
                print(f"selector: {selector}")
                if not selector:
                    errors.append(f"Empty selector for field: {key}")
                    continue

                try:
                    elements = soup.select(selector)
                    
                except SelectorSyntaxError:
                    errors.append(f"Empty selector for field {key}': {selector}")
                    continue

                if elements:

                    field_type = value.get(bin_keys.FIELD_TYPE, bin_keys.FIELD_TYPE_TEXT)

                    match field_type:

                        case bin_keys.FIELD_TYPE_TEXT:
                            answer = elements[0].get_text(strip=True)
                        
                        case bin_keys.FIELD_TYPE_LIST_TEXT:
                            answer = [e.get_text(strip=True) for e in elements]

                        case bin_keys.FIELD_TYPE_ATTRIBUTE:
                            answer = elements[0].get(value[bin_keys.FIELD_TYPE_ATTRIBUTE])
                        
            if answer is None:
                errors.append(f"Missing field: {key}")

            result[key] = answer
        
        result["_errors"] = errors

        return result