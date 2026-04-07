# Bin
A bin is a YAML config file that defines how the data will be retrieved, processed, and stored.

## Structure
It is first composed of different sections:
- A header
- Parameters
- Endpoints
- Filters

### Header

It contains basic information about the bin and the author:

```yaml
name: imdb
url: "https://www.imdb.com"
author:
  name: "trevor"
  website: "https://github.com/tru3v0r/"
version: 0.0.1
comment: "The first raccoonz bin ever."
```

### Parameters

The first section determines which modules are used for our two steps:
- fetcher: the module that retrieves the raw data (the DOM)
- the parser: the module that processes the data.

```yaml
fetcher: playwright
parser: bs4

fetch:
  scroll_to:
    select:
      css: "[data-testid='storyline-plot-summary']"
  wait_ms: 1500
```

### Endpoints

---

### Pipeline

#### Select

#### Extract

#### Filter

#### Type