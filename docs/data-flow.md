# Data flow
This page aims to explain how data is handled by the Raccoon class.


You might want to read the [glossary](glossary.md) first to get some concepts explained here.



## Object life cycle


### Initialization

```mermaid
flowchart TD

    %% INIT FLOW
    subgraph Init

        direction TD

        A[Init] --> B{packing_mode?}
        B -- eager --> C[_pack: load all nest to bag]
        B -- lazy --> D[Continue]
    end

```


### `dig()`

```mermaid
flowchart TD

    subgraph dig
        direction TB
        E[dig called] --> F{refresh?}

        F -- True --> G[Fetch HTML]
        G --> H[Move old raw to /_expired/ with timestamp]
        H --> H2[Write raw to nest/bin/lang/endpoint/raw]
        H2 --> I[Parse HTML]
        I --> J[Move old data to data/_expired with timestamp]
        J --> J2[Write data to nest/bin/lang/endpoint/data]
        J2 --> K[Store in bag]
        K --> L[Return data]

        F -- False --> M{packing_mode?}

        M -- eager --> N{Data in bag?}
        N -- Yes --> L
        N -- No --> G

        M -- lazy --> O[_pack_one: check/load from nest]
        O --> P{Data now in bag?}
        P -- Yes --> L
        P -- No --> G
    end
```