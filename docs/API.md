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
  - [serve](#serve)
    - [Description](#description-2)
    - [Parameters](#parameters-2)
      - [endpoint](#endpoint-1)
      - [port](#port)
  - [sniff](#sniff)
    - [Description](#description-3)

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

## serve

### Description

```python

```

### Parameters

#### endpoint

#### port

---

## sniff

### Description

```python

```