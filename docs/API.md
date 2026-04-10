# Raccoonz

## Table of contents

- [Raccoonz](#raccoonz)
  - [Table of contents](#table-of-contents)
  - [Constructor](#constructor)
    - [Description](#description)
    - [Parameters](#parameters)
      - [bin](#bin)
      - [packing\_mode](#packing_mode)
      - [debug](#debug)
  - [dig](#dig)
    - [Description](#description-1)
    - [Parameters](#parameters-1)
      - [endpoint](#endpoint)
      - [refresh](#refresh)
      - [lang](#lang)
      - [result\_type](#result_type)
      - [Other parameters](#other-parameters)
  - [nudge](#nudge)
    - [Description](#description-2)
    - [Parameters](#parameters-2)
  - [serve](#serve)
    - [Description](#description-3)
    - [Parameters](#parameters-3)
      - [bin](#bin-1)
      - [bins](#bins)
      - [endpoint](#endpoint-1)
      - [endpoints](#endpoints)
      - [port](#port)
    - [Call the API](#call-the-api)
      - [Endpoint format](#endpoint-format)
      - [Parameters](#parameters-4)
  - [sniff](#sniff)
    - [Description](#description-4)
    - [Parameters](#parameters-5)
      - [url](#url)
      - [dig](#dig-1)
      - [lang (🚧WIP)](#lang-wip)

---
## Constructor

### Description

```python
__init__(
    bin: str,
    packing_mode: str,
    debug: bool,
    **params
)
```

### Parameters

#### bin

#### packing_mode

#### debug

---

## dig

Returns the data from an endpoint with specific parameters.

### Description
```python
dig(
    endpoint: str,
    refresh: bool,
    lang: str,
    result_type: str,
    **params
) --> dict|Object
```

### Parameters

#### endpoint

#### refresh

#### lang

#### result_type

#### Other parameters

Most endpoint links have a customer parameter that you need to pass to retrieve the data.

---

## nudge

### Description

```python
nudge(
  bin: str,
  endpoint: str,
  lang: str
)
```

### Parameters


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

#### bin
Targets a unique bin you want to serve. If no `endpoint` or `endpoints` are defined, the whole bin will be served.

#### bins
Targets a list of bins you want to serve.

#### endpoint
In the case of a unique `bin` passed as parameter, targets a single endpoint to serve.

#### endpoints
In the case of a unique `bin` defined as parameter, targets a list of endpoints you want to serve within this bin.

#### port
The port on which you want to serve the API. By default, it is set as 8000.


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
- if set to `True`, `dig()` is called and and this will return the result:
```python
{'title': ['The Lord of the Rings: The Fellowship of the Ring'], 'year': ['2001'], ... }
```
- if set to `False`, returns information about the endpoint:
```python
{'bin': 'imdb', 'endpoint': 'movie', 'params': {'id': 'tt0340377'}}
```

#### lang (🚧WIP)