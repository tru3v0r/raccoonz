<img src="docs/images/logo-with-name.png">

# raccoonz
**raccoonz** is a Python library that extracts structured data from any website using **bins** (YAML config files) and serves it as an API.


## Installation (🚧WIP)
```bash
pip install raccoonz
```

## Quick Start
Let's take an example with a website that doesn't let us use their API anymore.

```python
from raccoonz import Raccoon

albert = Raccoon()
albert.sniff("https://www.imdb.com/title/tt0120737/")
albert.serve()
```

Then in your CLI:

```bash
curl "http://localhost:8000/imdb/movie?id=tt0120737"
```

This will return the full data:

```python
{
  "title": "The Lord of the Rings: The Fellowship of the Ring",
  "year": 2001,
  "certificate": "PG-13",
  "length": "2h 58m",
  "rating": {
    "note": 8.9,
    "votes": {
      "count": "2201.3K",
      "chart": [31893, 8255, 9979, 13497, 28184, 59051, 170013, 410445, 610992, 859085]
    },
    "reviews": "6K"
  },
  "interests": [
    "Action Epic",
    "Adventure Epic",
    "Dark Fantasy",
    (...)
  ],
  (...)
}
```

For more information see the [workflow](docs/how-it-works.md) page of the documentation.

## How does it work?

It uses YAML config files named **bins**.

### Bins
Bins are YAML files that contain all the information to properly retrieve data from a website. Here is a simplified example of `imdb.yaml` using CSS selectors:

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
        _select:
          css:
            - "[data-testid='hero__primary-text']"
      year:
        _select:
            css:
              - "h1 + ul[role='presentation'] li:first-child"
        _type: int
```

For the full bin specs, please read the [Bin section](docs/bin.md) of the documentation.

---

## Dependencies

raccoonz could not exist without these brilliant open-source libraries:

- [Pyyaml](https://pypi.org/project/PyYAML/) (used to read bins)
- [Requests](https://pypi.org/project/requests/) (used as the "basic" fetcher)
- [Playwright](https://pypi.org/project/playwright/) (used as the "advanced" fetcher)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) (used as the default parser)
- [FastAPI](https://pypi.org/project/fastapi/) (used to set up the API)
- [uvicorn](https://pypi.org/project/uvicorn/) (used to run the API)

---

## Documentation

If you need any further information, please read the complete [documentation](docs/index.md).

You will find a step-by-step guide that will help you dive into the library:

#### Basics
- [Glossary](docs/glossary.md): what the main concepts are
- [How it works](docs/how-it-works.md): how the workflow is built
- [API](docs/api.md): how to use the `Raccoon` class methods

#### To go further
- [Architecture](docs/architecture.md): how objects interact with each other
- [Data flow](docs/data-flow.md): how data is stored and loaded in the library
- [Bin](docs/bin.md): how to retrieve data using a bin, and how to write one