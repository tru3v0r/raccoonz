# Raccoonz

## Table of contents

- [Raccoonz](#raccoonz)
  - [Table of contents](#table-of-contents)
  - [Constructor](#constructor)
    - [Description](#description)
    - [Parameters](#parameters)
      - [packing\_mode](#packing_mode)
      - [debug](#debug)
  - [dig](#dig)
    - [Description](#description-1)
    - [Parameters](#parameters-1)
      - [bin](#bin)
      - [endpoint](#endpoint)
      - [refresh](#refresh)
      - [lang](#lang)
      - [result\_type](#result_type)
      - [Other parameters](#other-parameters)
  - [serve](#serve)
    - [Description](#description-2)
    - [Parameters](#parameters-2)
      - [bin](#bin-1)
      - [bins](#bins)
      - [endpoint](#endpoint-1)
      - [endpoints](#endpoints)
      - [port](#port)
    - [lang](#lang-1)
    - [Call the API](#call-the-api)
      - [Endpoint format](#endpoint-format)
      - [Parameters](#parameters-3)
      - [Data update while serving](#data-update-while-serving)
  - [sniff](#sniff)
    - [Description](#description-3)
    - [Parameters](#parameters-4)
      - [url](#url)
      - [dig](#dig-1)
      - [lang (🚧WIP)](#lang-wip)

---
## Constructor

### Description

```python
__init__(
    packing_mode: str,
    debug: bool,
    **params
)
```

### Parameters

| Param        | Type  | Allowed values  | Default | Example   |
|--------------|-------|-----------------|---------|-----------|
| packing_mode | str   | `eager`, `lazy` | `lazy`  | `eager`   |
| debug        | bool  | `True`, `False` | `False` |-          |
| params       | dict  | any             | -       |           |


#### packing_mode
The way data stored in the nest is added to the bag (the cache).

<u>Allowed values</u>: `eager`, `lazy` (default)
- `eager`: all the data is loaded during instantiation
- `lazy`: data is loaded when requested, if available


#### debug
<u>Allowed values</u>: `True`, `False` (default)
- `True`: enables debug mode (verbose logging, diagnostics)
- `False`: disables debug mode



---
## dig
Returns the data from an endpoint with specific parameters.


### Description
```python
dig(
    bin: str,
    endpoint: str,
    refresh: bool,
    lang: str,
    result_type: str,
    **params
) --> dict|Object
```


### Parameters

| Param        | Type  | Allowed values          | Default | Example          |
|--------------|-------|-------------------------|---------|------------------|
| bin          | str   | any bin in `src/bins/`  | -       | `users`          |
| endpoint     | str   | any endpoint in the bin | -       | `list`           |
| refresh      | bool  | `True`, `False`         | `False` | `True`           |
| lang         | str   | BCP 47 locale codes     | `en-US` | `fr-FR`          |
| result_type  | str   | `json`, `object`, `csv` | `json`  | `csv`            |
| params       | dict  | any                     | -       | `id="tt0120737"` |


#### bin
The name of the YAML file you want to use.

<u>Allowed values</u>: any bin you have in your `src/bins/` directory.


#### endpoint
The name of the endpoint which data you want to retrieve.

<u>Allowed values:</u> any endpoint defined in your bin.


#### refresh
<u>Allowed values</u>: `True`, `False` (default)
- `True`: forces a call to remote endpoint, even if data is available locally.
- `False`: uses local data if available.


#### lang
The language you want to retrieve the data in.
<u>Allowed values</u>: [BCP 47 locale codes](https://www.rfc-editor.org/info/bcp47) (e.g. `en-US` (default), `en-GB`, `fr-FR`, `fr-CA`, `es-ES`, `es-MX`, `de-DE`, `it-IT`, `ja-JP`, `zh-CN`, `zh-TW`, `ar-MA`...)

Note: the website might not be able to serve the data in the locale you picked.


#### result_type
The format you want the data to be returned in.

<u>Allowed values</u>: `json` (default), `object`, `csv`
- `json`: returns a JSON string
- `object`: returns a native `Object()` object, with parameters accessible as attributes:
```python
albert = Raccoon()
movie = albert.dig("imdb", "movie", id="tt0120737", result_type="object")
print(movie.title)
print(movie.rating.note)
```
This will return:
```python
['The Lord of the Rings: The Fellowship of the Ring']
['8.9']
```
- `csv`: returns a CSV string.


#### Other parameters

As you can see in the [Path](bin.md#path) section of the Bin documentation, endpoints can be **dynamic**, which means they need a custom parameter to retrieve data. You need to pass it explicitly in the arguments:
```python
albert = Raccoon()
movie = albert.dig("imdb", "movie", id="tt0120737")
```

---

## serve

Allows you to serve data as an API.


### Description

```python
  serve(
      bin: str,
      bins: list,
      endpoint: str,
      endpoints: list,
      lang: str,
      port: str
  ):
```

### Parameters

| Param     | Type | Allowed values                | Default | Example     |
|-----------|------|-------------------------------|---------|-------------|
| bin       | str  | any bin in `src/bins/`        | -       | `users`     |
| bins      | list | any bins in `src/bins/`       | -       | `["users"]` |
| endpoint  | str  | any endpoint in selected bin  | -       | `list`      |
| endpoints | list | any endpoints in selected bin | -       | `["list"]`  |
| lang      | str  | BCP 47 locale codes           | `en-US` | `fr-FR`     |
| port      | str  | valid port number             | `8000`  | `"8080"`    |


#### bin
Targets a unique bin you want to serve. If no `endpoint` or `endpoints` are defined, the whole bin will be served.

<u>Allowed values</u>: any bin you have in your `src/bins/` directory.


#### bins
Targets a list of bins you want to serve.

<u>Allowed values</u>: any bin you have in your `src/bins/` directory.


#### endpoint
In the case of a unique `bin` passed as parameter, targets a unique endpoint from selected bin.

<u>Allowed values:</u> any endpoint defined in your bin.


#### endpoints
In the case of a unique `bin` defined as parameter, targets a list of endpoints you want to serve within this bin.

<u>Allowed values:</u> any endpoints defined in your bin.

#### port
The port on which you want to serve the API. By default, it is set as 8000.

### lang
The language you want to serve the data in.
<u>Allowed values</u>: [BCP 47 locale codes](https://www.rfc-editor.org/info/bcp47) (e.g. `en-US` (default), `en-GB`, `fr-FR`, `fr-CA`, `es-ES`, `es-MX`, `de-DE`, `it-IT`, `ja-JP`, `zh-CN`, `zh-TW`, `ar-MA`...)

### Call the API

#### Endpoint format
The API URL format is as follows:

- `http://localhost:<port>/<bin>/<endpoint>/<field>(/<subfield>/)`

So for example, using the imdb bin, this endpoint:
- `http://localhost:8000/imdb/movie/title/?id=tt0120737`

Will return this data:
```json
["The Lord of the Rings: The Fellowship of the Ring"]
```

#### Parameters

Parameters such as the `{endpoint path param}` (see **Dynamic path** in the [Path](bin.md#path) section of the Bin documentation) and `lang` are passed as follows:
- `.../<field>?{endpoint path param}=<value>&lang=<lang>`

By default, `lang` is set to `en-US`.

An endpoint with a `lang` parameter:
- `http://localhost:8000/imdb/movie/title/?id=tt0120737&lang=fr-FR`

Will return:
```json
["Le Seigneur des anneaux : La Communauté de l'anneau"]
```

#### Data update while serving
As served data is loaded to and accessed from the bag, externally updating the nest  results in an inconsistency between the updated and the served data. To avoid this, you can nudge the Raccoon, i.e. contact the API to inform it that some data has been updated:
```bash
curl http://localhost:8000/imdb/top250movies/_nudge
```

Or even with parameters:
```bash
curl http://localhost:8000/imdb/movie/_nudge?id=tt0120737
```

The Raccoon will then reload the updated data to the bag.

---
## sniff
Reverse-matches a URL to an endpoint defined in your `/bins` directory.

### Description

```python
sniff(
  url: str,
  dig: bool,
  lang: str
)
```

### Parameters

| Param | Type | Allowed values      | Default | Example                    |
|-------|------|---------------------|---------|----------------------------|
| url   | str  | valid URL           | -       | `imdb.com/title/tt0120737` |
| dig   | bool | `True`, `False`     | `False` | -                          |
| lang  | str  | BCP 47 locale codes | `en-US` | `fr-FR`                    |


#### url
The URL you want to test against your bins.
Schemes like `https://` or `http://`, the `www` subdomain  and the end slash `/` are optional, so these examples will return the exact samematch:
- `https://www.imdb.com/title/tt0120737/`
- `https://imdb.com/title/tt0120737`
- `http://www.imdb.com/title/tt0120737/`
- `http://imdb.com/title/tt0120737`
- `www.imdb.com/title/tt0120737`

#### dig
In case of a match, defines if [dig()](#dig) must be performed on the matching endpoint.

<u>Allowed values</u>: `True`, `False`
- `True`: calls `dig()` and returns the result:
```python
{'title': ['The Lord of the Rings: The Fellowship of the Ring'], 'year': ['2001'], ... }
```
- `False`: returns information about the endpoint:
```python
{'bin': 'imdb', 'endpoint': 'movie', 'params': {'id': 'tt0340377'}}
```

#### lang (🚧WIP)
The language the data is retrieved in.
<u>Allowed values</u>: [BCP 47 locale codes](https://www.rfc-editor.org/info/bcp47) (e.g. `en-US` (default), `en-GB`, `fr-FR`, `fr-CA`, `es-ES`, `es-MX`, `de-DE`, `it-IT`, `ja-JP`, `zh-CN`, `zh-TW`, `ar-MA`...)