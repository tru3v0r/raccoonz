# Bin

## Table of contents

- [Bin](#bin)
  - [Table of contents](#table-of-contents)
  - [Description](#description)
  - [Structure](#structure)
  - [Header](#header)
    - [Parameters](#parameters)
    - [Example](#example)
  - [Data access](#data-access)
    - [Parameters](#parameters-1)
    - [Example](#example-1)
  - [Endpoints](#endpoints)
    - [Parameters](#parameters-2)
    - [Path](#path)
      - [Static](#static)
      - [Dynamic](#dynamic)
    - [Fields](#fields)
      - [Example](#example-2)
  - [Operators](#operators)
    - [Shape operators](#shape-operators)
      - [Parameters](#parameters-3)
      - [`_group`](#_group)
        - [Example](#example-3)
      - [`_map`](#_map)
        - [Parameters](#parameters-4)
        - [Example](#example-4)
    - [Field operators](#field-operators)
      - [Parameters](#parameters-5)
      - [`_select`](#_select)
        - [Parameters](#parameters-6)
        - [Example](#example-5)
      - [`_extract`](#_extract)
        - [Parameters](#parameters-7)
        - [Example](#example-6)
      - [`_filter`](#_filter)
        - [Parameters](#parameters-8)
        - [Example](#example-7)
      - [`_type`](#_type)
        - [Parameters](#parameters-9)
        - [Example](#example-8)
  - [Filters](#filters)
    - [Parameters](#parameters-10)

## Description
A bin is a YAML config file that defines how the data will be retrieved, processed, and stored.


## Structure

It is first composed of different sections:
- A [header](#header)
- [Data access](#data-access)
- [Endpoints](#endpoints)
- [Filters](#filters)


## Header
It contains basic information about the bin and the author:

### Parameters
| Key       | Type | Description   | Example                |
|-----------|------|---------------|------------------------|
| `name`    | str  | bin name      | `imdb`                 |
| `url`     | str  | base URL      | `https://www.imdb.com` |
| `author`  | dict | author info   | `{name,website}`       |
| `version` | str  | bin version   | `0.0.1`                |
| `comment` | str  | optional note | `"first bin"`          |

### Example

```yaml
name: imdb
url: "https://www.imdb.com"
author:
  name: "trevor"
  website: "https://github.com/tru3v0r/"
version: 0.0.1
comment: "The first raccoonz bin ever."
```

---

## Data access
This section determines which modules are used for fetching and parsing data:
- The **fetcher**: the module that retrieves the raw data (the DOM)
- The **parser**: the module that processes the data.


### Parameters
| Param     | Type | Allowed values           | Default    | 
|-----------|------|--------------------------|------------|
| `fetcher` | str  | `requests`, `playwright` | `requests` |
| `parser`  | str  | `bs4`                    | `bs4`      |


### Example

```yaml
fetcher: playwright
parser: bs4
```

---

## Endpoints

An endpoint refers to a page displaying content.
It is composed of two elements:
- A path
- Fields


### Parameters

| Key      | Type | Allowed values                | Example        |
|----------|------|-------------------------------|----------------|
| `path`   | str  | static or `{param}` template  | `/title/{id}/` |
| `fields` | dict | any string without special YAML characters (`#`, `!`, `&` or `*`)   | `{title:...}`  |


### Path

The path is the URL part that comes after the domain name. It can be of two types:
- Static
- Dynamic

#### Static
A static path points to a unique page that does not require any additional parameter, such as follows:

```yaml
endpoints:
  top250movies:
    path: "/chart/top/"
```

The endpoint is then called using this:

```python
albert.dig("imdb", "top250movies")
```

#### Dynamic
A dynamic path points to a template page that displays content based on a dynamic parameter, like an id or a slug. You can declare it using brackets `{}`:

```yaml
endpoints:
  movie:
    path: "/title/{id}/"
```

 The parameter `id` needs then to be passed to the method:

```python
albert.dig("imdb", "movie", id="tt0120737")
```


### Fields

The fields are the actual data containers of the page.
You are free to name them however you want, as long as it does not collide with YAML special characters, like `#`, `!`, `&` or `*`. However, it is not advised to prefix them with the underscore (`_`), as this character is visually associated with operators (see below).


#### Example

```yaml
endpoints:
  movie:
    fields:
      title: ...
      year: ...
      certificate: ...
      ...
```

 You can nest them as many times as your data structure requires it.

---

## Operators

Operators are YAML keys that perform operations on the data. By convention ,they start with the underscore `_`.

There are two sorts of operators:
- Shape operators
- Field operators


### Shape operators
Shape operators control **how** data is structured in the final result.


#### Parameters

| Operator   | Description            | Allowed values |
|------------|------------------------|----------------|
| `_group`   | Groups data            | -              |
| `_key`     | Defines key mapping    | Any string without YAML characters |
| `_value`   | Defines value mapping  | Any string without YAML characters |


#### `_group`

Allows you to group different datasets in the same group.

| Key       | Description | Allowed values |
|-----------|-------------|----------------|
| `_select` | Selector pointing to the container where input data groups are located. | See [_select](#_select) |
| `fields`  | Fields to include in the output data group. |


##### Example

Declaring this in your bin:

```yaml
        actors:
          _group:
            select:
              css:
                - "[data-testid='title-cast'] [data-testid='title-cast-item']"
            fields:
              name: (...)
              id: (...)
              link: (...)
              role: (...)
```

will return:

```yaml
(...)
  actors:
  - name: Elijah Wood
    id: nm0000704
    link: /name/nm0000704/
    role: Frodo
  - name: Ian McKellen
    id: nm0005212
    link: /name/nm0005212/
    role: Gandalf
  - (...)
```

**Note**: fields are processed normally, so you can include any [field operator](#field-operators) pipeline you want.


#### `_map`

The `_map` shape operator maps data into key-value pairs, where `_select` points at the container where keys and values are located, then the value retrieved by `_key` becomes the key, and `_value` defines the associated value.


##### Parameters

| Operator   | Description            | Allowed values |
|------------|------------------------|----------------|
| `_select`     | Selector pointing to the container where keys and values are located. | See [_select](#_select) |
| `_key`     | Defines key mapping    | Any string without YAML characters |
| `_value`   | Defines value mapping  | Any string without YAML characters |

##### Example
The example below:
```yaml

```

will return:

```yaml

```

### Field operators
Field operators compose a pipeline that controls **what** data is retrieved from the DOM. There are four:
- `_select`
- `_extract`
- `filter`
- `_type`


#### Parameters

| Operator   | Type | Allowed values   | Default | Example        |
|------------|------|------------------|---------|----------------|
| `_select`  | dict | `css`            | -       | `{css:[...]}`  |
| `_extract` | dict | `text`, `attr`   | `text`  | `{attr:href}`  |
| `_filter`  | str  | any filter defined in the bin [filters](#filters) section  | -       | `clean_link`   |
| `_type`    | str  | `string`,`int`,`float`,`bool` | `string` | `_type: bool` |


#### `_select`

Fields need **at least** a `_select` field operator to work with.


##### Parameters


| Key    | Allowed values         | Example |
|--------|------------------------|---------|
| `css`  | Any valid css selector | <ul><li>`[data-testid='hero__primary-text']`</li><li>`[data-testid^='rating-histogram-bar-']`</li></ul> |


##### Example

```yaml
    fields:
      title:
        _select:
          css:
            - "[data-testid='hero__primary-text']"
            - "h1 span"
```

The example above shows a list of two CSS selectors, so that if the first one does not return any value (which can be common as some websites often change their DOM), another selection attempt is performed with the second one. You can add as many as you want.


#### `_extract`
By default, the data extracted from the `_select` operator is the selected element's **inner text**. However, you can extract other types of data from this element using `_extract`.

##### Parameters

| Operator   | Type | Allowed values   | Default | Example        |
|------------|------|------------------|---------|----------------|
| `_extract` | dict | `text`, `attr`   | `text`  | `{attr:href}`  |

| Key      | Allowed values     |
|----------|--------------------|
| `text`   | -                  |
| `attr`   | `href`             |

##### Example
Let's say you want to extract to extract the URL located in a hyperlink:

```yaml
      link:
        _select:
          css:
            - "a[data-testid='title-cast-item__actor']"
        _extract:
          attr: href
```
This will extract the `href` attribute value from the selected `a` tag.



#### `_filter`
The `_filter` operator allows you to perform a deeper layer of processing on data you extracted, to filter out elements you don't need.



##### Parameters

| Operator   | Type | Allowed values   | Default | Example        |
|------------|------|------------------|---------|----------------|
| `_filter`  | str  | any filter defined in the bin [filters](#filters) section  | -       | `clean_link`   |


##### Example

Let's say the data we extracted so far is not clean enough to be stored. We can perform an additional operation to filter out elements we don't need. In the case of our link, our current output will look like this:

`https://www.imdb.com/name/nm0000704/?ref_=tt_cst_t_1`

Which contains a lot of unnecessary elements:
- The domain name, that we alreay know from the bin `url` key
- the `?ref_=...` param, that we will not have the use of.

We then can use a `_filter` field operator in our pipeline:

```yaml
      link:
        _select:
          css:
            - "a[data-testid='title-cast-item__actor']"
        _extract:
          attr: href
        _filter: clean_link
```
The filter, which is declared in the [Filters](#filters) section of the bin, performs the cleaning operation to retrieve desired data:

`/name/nm0000704/`

There is one more operation to complete the pipeline, data casting.


#### `_type`

This final stage allows to force a certain type onto the data.

##### Parameters
| Operator   | Type | Allowed values   | Default | Example        |
|------------|------|------------------|---------|----------------|
| `_type`    | str  | `string`,`int`,`float`,`bool` | `string` | `_type: bool` |

##### Example
Let's take another example to illustrate this use case:

```yaml
      year:
        _select:
          css:
            - "h1 + ul[role='presentation'] li:first-child"
        _type: int
```

**Note**: you don't need a "list" type as if more than one element is retrieved from the endpoint, it will automatically return a list of the declared `type`.

---


## Filters

The last section of the bin allows to declare filters that can be called using `filter`, as seen in the [Filter](#filter) section of the Fields pipeline.


### Parameters

| Param | Description | Allowed values | Example |
|-------|-------------|----------------|---------|
| `regex` | Retrieves data using a regular expression. | Any valid regex | `^([^?]+)` |

**Note**: at the moment, the default catch group is 1.

```yaml
filters:

  extract_id_from_link:
    regex: "^(?:https://www\\.imdb\\.com)?/(?:title|name)/((?:tt|nm)\\d+)/"

  clean_link:
    regex: "^([^?]+)"

  vote_by_star:
    regex: "^(\\d+)"
```

---
