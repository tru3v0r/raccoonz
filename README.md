# raccoonz
raccoonz is a Python library that extracts structured data from any website using **bins** (YAML configs) and serves it as an API.

## How does it work?
Let's take as an example a website that doesn't let us use their API anymore.

### Installation (🚧WIP)
```bash
pip install raccoonz
```

### Quick Start
```python
from raccoonz import Raccoon

albert = Raccoon("imdb")
movie = albert.dig("movie", id="tt0120737")

print(movie)
```
This will print:
```json
{'title': 'The Lord of the Rings', 'year': 2001}
```

### Serve as API (🚧WIP)

```python
albert.serve()
```
Then in your CLI:
```bash
curl "http://localhost:8000/imdb/movie?id=tt0120737"
```
This will return the full data:
```json
{'title': 'The Lord of the Rings', 'year': 2001}
```

## Bins 🗑️✍️
Bins are YAML files that contain all the information to properly retrieve data from a website. Here is a simplified example of `imdb.yaml`:
```yaml
name: imdb
url: "https://www.imdb.com"

fetcher: playwright
parser: bs4

endpoints:
  movie:
    path: "/title/{id}/"
    fields:
      title:
        select:
          css:
            - "[data-testid='hero__primary-text']"
      year:
        select:
            css:
              - "h1 + ul[role='presentation'] li:first-child"
        type: int
```
For the bin full specs, please read the [bin section](docs/bin.md) of the documentation.

---

## Dependencies

raccoonz could not exist without these brilliant open-source libraries:
- [Pyyaml](https://pypi.org/project/PyYAML/) (used to read bins)
- [Requests](https://pypi.org/project/requests/) (used as the "basic" fetcher)
- [Playwright](https://pypi.org/project/playwright/) (used as the "advanced" fetcher)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) (used as the default parser)

---

## Documentation

If you need any further information, please read the complete [documentation](docs/index.md).