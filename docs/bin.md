# Bin

A bin is a YAML config file that defines how the data will be retrieved, processed, and stored.


## Structure

It is first composed of different sections:
- A header
- Parameters
- Endpoints
- Filters


## Header

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


---

## Parameters

The first section determines which modules are used for our two steps:
- The **fetcher**: the module that retrieves the raw data (the DOM). Possible values are `requests` and `playwright`.
- The **parser**: the module that processes the data. The only possible value so far is `bs4`.

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


### Path

The path is the URL part that comes after the domain name. It can be of two types:
- **Static**: points to a unique page that does not require any additional parameter, such as follows:
```yaml
endpoints:
  top250movies:
    path: "/chart/top/"
```

The endpoint is then called using this:
```python
albert.dig("top250movies")
```
- **Dynamic**: points to a template page that displays content based on a dynamic parameter, like an id or a slug. You can declare it using brackets `{}`:
```yaml
endpoints:
  movie:
    path: "/title/{id}/"
```
 The parameter `id` needs then to be passed to the method:
```python
albert.dig("movie", id="tt0120737")
```


### Fields

The fields are the actual data containers of the page.
You are free to name them however you want, as long as it does not collide with YAML special characters, like `#`, `!`, `&` or `*`. However, it is not advised to prefix them with the underscore (`_`), as this character is visually associated with operators (see below).
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

#### Operators

- Shape operators: they control **how** data is structured in the final result. There are three: `_group`, `_key`, and `_value`.
- Field operators : they compose a pipeline that controls **what** data is retrieved from the DOM. There are four: `_select`, `_extract`, `filter`, and `_type`.


##### Shape operators

###### _group

###### _key

###### _value


##### Field operators

###### _select

Fields need **at least** a `_select` field operator to work with. Currently, the only supported selector type is `css`:
```yaml
    fields:
      title:
        _select:
          css:
            - "[data-testid='hero__primary-text']"
            - "h1 span"
```
The example above shows a list of two CSS selectors, so that if the first one does not return any value (which can be common as some website often change their DOM), another selection attempt is performed with the second one. You can add as many as you want.


###### _extract

By default, the data extracted from the `_select` operator is the selected element's **inner text**. However, you can extract data from another attribute:
```yaml
      link:
        _select:
          css:
            - "a[data-testid='title-cast-item__actor']"
        _extract:
          attr: href
```
This will extract the `href` attribute value from the selected `a` tag.

Curently, only `attr` is supported for the `_extract` control, and its only accepted value is `href`.

###### _filter

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


###### _type

This final stage allows to force a certain type onto the data. Let's take another example to illustrate this use case:

```yaml
      year:
        _select:
          css:
            - "h1 + ul[role='presentation'] li:first-child"
        _type: int
```
`_type` values accepted: `text` (by default), `int`, `float` and `bool`.

Note: you don't need a "list" type as if more than one element is retrieved from the endpoint, it will automatically return a list of the declared `type`.

---


## Filters

The last section of the bin allows to declare filters that can be called using `filter`, as seen in the [Filter](#filter) section of the Fields pipeline.

Currently, only the `regex` type is supported.

Note: at the moment, the default catch group is 1.

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
