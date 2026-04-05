from dataclasses import dataclass

@dataclass
class Record:
    def __init__(self, params, url, html, data, timestamp, lang):
        self.params = params
        self.url = url
        self.html = html
        self.data = data
        self.timestamp = timestamp
        self.lang = lang