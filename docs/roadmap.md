# Roadmap

This page outlines the project’s direction, from its current state to its long-term vision.

To get the big picture, Raccoonz is driven by the idea of a free internet, where data is accessible to everyone. In a world where a few actors decide what data is shared, the most sustainable way to ensure its access is to decentralize it.


## v0.1.0 - Core (done)

The **core** phase:
- [x] Bins
- [x] `dig()`
- [x] `sniff()`
- [x] `serve()`
- [x] Cache (TTL + hash)


## v0.2.x - Hardening

The **stabilization** phase:

- [ ] Tests
- [ ] CLI
- [ ] Validation
- [ ] Cache improvements
- [ ] Hooks system


## v0.3.x - Market

The **distribution** phase:

- [ ] Bin publication
- [ ] Bin discovery
- [ ] Remote fallback via `forage()`


## v0.4.x - Lazer

The **creation** phase:

- [ ] Browser extension
- [ ] Visual bin builder
- [ ] Live preview
- [ ] Publishing to Market


## v0.5.x - Forage

The **intelligence** phase:

- [ ] Fallback when `sniff()` fails
- [ ] Automatic Market bin retrieval
- [ ] Local caching of remote bins


## v0.6.x - Warren

The **foundation** phase:

- [ ] Introduce DEN (Data Exchange Node)
  - run Raccoon as a network node
  - expose local data via API

- [ ] Basic peer communication
  - query other DENs for data
  - simple request/response model

- [ ] Initial peer discovery
  - bootstrap from known nodes


## v0.7.x - Warren

The **expansion** phase:

- [ ] Advanced peer discovery
  - find DENs serving a bin/endpoint
  - dynamic peer list

- [ ] Data sharing
  - share cached records between nodes
  - optional response caching from peers

- [ ] Bin distribution over network
  - fetch bins from peers (not only Market)


## v1.0.0 - Warren

The **stability** phase:

- [ ] Trust & integrity
  - signed bins
  - optional peer trust policies

- [ ] Network reliability
  - fallback between multiple peers
  - timeout / retry strategies

- [ ] Stable decentralized data exchange
  - consistent peer-to-peer behavior
  - production-ready network layer