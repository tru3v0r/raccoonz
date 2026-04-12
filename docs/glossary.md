# Glossary

The **raccoonz** library borrows from the semantic field of this sneaky, yet beloved animal. It [sniffs](#sniff), [digs](#dig) through [bins](#bin), [stashes](#stash) data in its [bag](#bag) and [hoards](#hoard) it in its [nest](#nest) to [pack](#pack) it later. If it's in a good mood, it might even [serve](#serve) the data.

## Table of contents
- [Glossary](#glossary)
  - [Table of contents](#table-of-contents)
  - [bag](#bag)
  - [bin](#bin)
  - [dig](#dig)
  - [endpoint](#endpoint)
  - [fetcher](#fetcher)
  - [hoard](#hoard)
  - [nest](#nest)
  - [nudge](#nudge)
  - [pack](#pack)
  - [parser](#parser)
  - [serve](#serve)
  - [sniff](#sniff)
  - [stash](#stash)


## bag
The bag is the instantiated `Raccoon` object's cache.


## bin
A bin is a YAML config file that defines how data should be retrieved, processed and structured.

Bins are located in `src/raccoonz/bins/`.

For the structure of a bin, see [Bin](bin.md).


## dig
Digging is the action of retrieving data from a website using a [bin](#bin), or from the [bag](#bag).

`dig()` is the `Raccoon` class method that performs this action.

See the [dig()](API.md#dig) section of the `Raccoon` [API documentation](API.md).


## endpoint
In a [bin](bin.md), an endpoint is a page containing data ready to be retrieved.

See the [Endpoints section](bin.md#endpoints) of the [bin documentation](bin.md).


## fetcher
The fetcher is the tool defined in a [bin](#bin) used to retrieve raw data (DOM). It is then sent to the [parser](#parser) to be processed and structured.

See the [Data access](bin.md#data-access) section of the [bin documentation](bin.md).


## hoard
`_hoard()` is the `Raccoon` class helper method that writes freshly-retrieved data into the [nest](#nest).


## nest
The nest is the directory where all retrieved data is stored.
It is located in `src/raccoonz/nest/`.


## nudge
Nudging is the action of signaling a Raccoon that data has been externally updated in the nest, prompting it to update its [bag](#bag). It is done calling the [endpoint] concerné, with relevant params.


`_nudge()` is the `Raccoon` helper method then called to perform the data update.

See [Data update while serving](API.md#data-update-while-serving).


## pack
Packing is the action of filling up the instantiated `Raccoon` object's [bag](#bag) with [nest](#nest) data, i.e. loading stored data in cache.

`_pack` is the `Raccoon` helper method that loads the cache.

When instantiating a new `Raccoon` object, the `packing_mode` argument setting defines how the bag is filled: `lazy` or `eager` (see the [Constructor](API.md#constructor) section of the `Raccoon` API)


## parser
The parser is the tool defined in a [bin](bin.md) to process and structure data retrieved by the [fetcher](#fetcher).

See the [Data access](bin.md#data-access) section of the [bin documentation](bin.md).


## serve
Serving is the action of exposing data on endpoints as an API.

`serve()`is the `Raccoon` class method that performs this action.

See the [serve()](API.md#serve) section of the `Raccoon` [API documentation](API.md).


## sniff
Sniffing is the action of reverse-matching a given URL.

`sniff()` is the `Raccoon` class method that performs this action. If the URL matches an [endpoint](#endpoint), it will retrieve data or return information about said endpoint, depending on set parameters.

See the [sniff()](API.md#sniff) section of the `Raccoon` [API documentation](API.md).


## stash

Stashing is the action of filling the [bag](#bag) with freshly [dug](#dig) data, i.e. adding this data to the cache.

`_stash()` is the `Raccoon` class helper method that performs this action.