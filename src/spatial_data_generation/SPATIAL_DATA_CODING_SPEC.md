# SPATIAL_DATA_CODING_SPEC.md

## Purpose

This document specifies a coding approach for the spatial world abstraction defined in `SPATIAL_DATA_OVERVIEW.md`.

The goal is to provide a **generic, extensible, and testable** implementation of the following abstraction:

```text
Layer = (Domain, Features, Network?)
World = DAG of Layers via Portals
```

This spec is intentionally **light on repository/package structure** and **heavy on invariants, interfaces, and testing**. It is designed to support simulation, visualization, and future extension without baking scenario-specific concepts into the core model.

---

## Design Goals

The implementation should:

- represent the spatial abstraction faithfully
- keep geometry, topology, and hierarchy separate but composable
- remain generic at the core level
- be open to extension without frequent modification of existing core models
- support JSON configs as the primary user-facing configuration format
- use Pydantic models for validated configuration/data loading
- support visualization through separate adapters/renderers
- be developed test-first, with both unit and integration tests

---

## Non-Goals

This spec does **not** require:

- scenario-specific Python classes such as `Galaxy`, `Planet`, `City`, `Cantina`
- a single rendering backend
- runtime simulation logic in the core config layer
- a specific package layout
- immediate support for every possible geometry/domain type

---

## Core Abstraction

### World

The top-level validated configuration object should represent a world:

```text
WorldConfig
├── layers: list[LayerConfig]
├── portals: list[PortalConfig]
└── metadata?: dict
```

The world should satisfy:

- layer ids are unique
- portal ids are unique
- all portal source/target layers exist
- the portal-induced layer graph is acyclic

---

## Layer

Each layer should represent one spatial domain and its contents:

```text
LayerConfig
├── id: str
├── domain: DomainConfig
├── features: list[FeatureConfig]
├── network?: NetworkConfig
└── metadata?: dict
```

### Layer invariants

- feature ids are unique within a layer
- the geometry of every feature is valid within the layer's domain
- network references only valid nodes/features in the same layer

---

## Domain

A Domain is the geometry foundation of a layer.

The mathematically accurate mental model is:

```text
Domain = metric space, optionally equipped with an atlas
```

The implementation model should remain practical:

```text
DomainConfig = discriminated union by `type`
```

Initial supported domain types should be narrow and extensible, for example:

- `plane`
- `sphere`
- `abstract`

Each domain subtype should define only data intrinsic to that domain.

### Example fields

#### Plane domain
- `type`
- `metric`
- optional `bounds`
- optional dimensional metadata if needed later

#### Sphere domain
- `type`
- `metric`
- `radius`
- `coordinate_system`

#### Abstract domain
- `type`
- `metric`
- optional layout/render metadata

### Domain invariants

- `plane` coordinates are 2D
- `sphere` coordinates follow the declared convention
- bounds, if present, are well-formed
- unsupported coordinate shapes are rejected

---

## Features

A Feature is a typed object embedded in the layer domain.

The core implementation should avoid scenario-specific subclasses for semantic objects. The abstraction should be data-driven.

```text
FeatureConfig
├── id: str
├── kind: str
├── geometry_type: literal discriminator
├── geometry: geometry payload
├── properties?: dict
└── style?: dict
```

### Important rule

`kind` should remain a free semantic string such as:

- `planet`
- `settlement.city`
- `building.house`
- `furniture.chair`

This keeps the abstraction extensible without requiring a new Python class for each semantic type.

### Geometry primitives

Initial geometry primitives should be based on spatial form, not lore/semantics:

- `point`
- `path`
- `region`

This naturally suggests a discriminated union for `geometry_type`.

### Example geometry payloads

#### Point
```text
PointGeometry
└── coordinates: list[float]
```

#### Path
```text
PathGeometry
└── coordinates: list[list[float]]
```

#### Region
```text
RegionGeometry
├── shell: list[list[float]]
└── holes?: list[list[list[float]]]
```

### Feature invariants

- point coordinate dimensionality matches domain
- path coordinate dimensionality matches domain
- region shell is present and well-formed
- holes, if present, are well-formed
- geometry is valid in the domain
- feature ids are unique within a layer

---

## Network

A network defines traversable structure over the layer.

The core mental model is:

```text
Network is constrained by Domain and Features.
```

Implementation model:

```text
NetworkConfig
├── nodes: list[NetworkNodeConfig]
├── edges: list[NetworkEdgeConfig]
└── metadata?: dict
```

### Nodes

A node may be independent or associated with a feature.

```text
NetworkNodeConfig
├── id: str
├── feature_id?: str
├── properties?: dict
└── style?: dict
```

### Edges

```text
NetworkEdgeConfig
├── id: str
├── source: str
├── target: str
├── directed?: bool
├── weights?: dict[str, float]
├── properties?: dict
└── style?: dict
```

### Network invariants

- node ids are unique within the network
- edge ids are unique within the network
- every edge source/target references a valid node
- `feature_id`, if present, references a valid feature in the same layer
- weights are structurally valid
- network validity rules are checked after model parsing

### Design note

The network should not be treated as the owner of geometry. Instead:

- Domain + Features define feasible structure
- Network defines selected/allowed traversal

This allows:
- authored networks
- geometry-derived networks
- dynamically updated networks later

---

## Portals

Portals define hierarchy.

The precise model is:

```text
Portal = local map between subsets of domains
Hierarchy = DAG induced by portals over layers
```

Implementation model:

```text
PortalConfig
├── id: str
├── source_layer_id: str
├── target_layer_id: str
├── source_selector: dict
├── target_selector: dict
├── mapping?: dict
└── metadata?: dict
```

### Portal selectors

The first version should remain deliberately simple.

Initial selectors should likely support:
- `feature_id`
- optional `layer_entry` flag on target side

Richer subset mapping can come later.

### Portal invariants

- portal ids are unique
- source and target layers exist
- source selector resolves in source layer
- target selector resolves in target layer
- induced graph over layers is acyclic
- fan-in is allowed
- fan-out is allowed

---

## Parsing and Validation

The implementation should separate:

1. **schema validation**
2. **semantic validation**

### 1. Schema validation

Handled by Pydantic models:
- required fields
- types
- discriminated unions
- obvious local constraints

### 2. Semantic validation

Handled by separate validation functions/services:
- uniqueness checks across collections
- cross-reference validation
- portal DAG validation
- geometry/domain compatibility
- network/feature consistency

### Recommendation

Do not force all semantic validation into Pydantic field validators. Keep global validation logic separate and explicit.

A good conceptual flow is:

```text
read JSON -> deserialize -> parse Pydantic model -> semantic validate -> return validated world config
```

---

## Config Reader

The reader should remain thin.

### Responsibilities

- read JSON from disk
- deserialize into Python data
- parse into `WorldConfig`
- run semantic validation
- return validated config object

### Non-responsibilities

- rendering
- simulation
- scenario defaults
- mutation of the config into runtime state

### Supported input surface

At minimum:
- JSON file path
- Python dictionary

Potential future extension:
- YAML or TOML adapters that produce the same intermediate dict before Pydantic parsing

---

## Visualization

Visualization should be a separate concern from config loading and validation.

The visualizer should consume validated world/layer configs and produce artifacts.

### Design rule

Visualizers interpret the abstraction. They do not redefine it.

### Recommended initial renderers

#### 1. Matplotlib static renderer
Best first renderer for:
- plane layers
- simple graph overlays
- tests
- documentation examples

#### 2. Plotly interactive renderer
Useful for:
- demos
- hover labels
- zoom/pan
- exploration of example worlds

#### 3. Graph-focused renderer
Useful for:
- abstract domains
- topology-first layers
- network-heavy examples

#### 4. Sphere projection renderer
Useful for:
- sphere domains
- 2D projected views of spherical data

### Renderer expectations

A renderer should:
- accept validated config
- fail clearly on unsupported domain/geometry combinations
- support basic styling overrides
- not mutate the source config

### Design note

Do not hardcode scenario semantics such as “galaxy renderer” or “city renderer” into the core model. Those can exist as presets/options in the visualization layer.

---

## Examples

Examples should live outside the main source tree and demonstrate the abstraction from a user perspective.

Each example should include:
- a JSON config
- a minimal runner entrypoint or usage snippet
- expected artifact(s), if appropriate
- brief documentation

### Required examples

At minimum, include and maintain examples equivalent to:

- Austin example
- Earth example
- Milky Way example

These examples should remain small, standalone, and easy to parse/render.

### Example design goal

A user should be able to:
1. write a JSON config
2. call the reader
3. call a renderer
4. obtain a valid world artifact

with minimal boilerplate

---

## Testing Strategy

Testing should be written first where possible.

The implementation should include both **unit tests** and **integration tests**.

---

## Unit Tests

Unit tests should verify the behavior and invariants of the data model and validation logic.

### Domain tests
- valid plane domain parses
- valid sphere domain parses
- valid abstract domain parses
- invalid domain type fails
- invalid coordinate system fails where applicable
- invalid bounds fail

### Feature tests
- point feature parses in valid domain
- path feature parses in valid domain
- region feature parses in valid domain
- invalid coordinate dimensionality fails
- malformed shell/holes fail
- duplicate feature ids in a layer fail semantic validation

### Network tests
- valid network parses
- duplicate node ids fail
- duplicate edge ids fail
- edge referencing unknown node fails
- node referencing unknown feature fails
- weights validate as expected

### Portal tests
- valid portal parses
- unknown source layer fails
- unknown target layer fails
- bad source selector fails
- bad target selector fails
- portal cycle fails DAG validation
- fan-in is permitted

### World validation tests
- duplicate layer ids fail
- duplicate portal ids fail
- valid multi-layer world passes
- acyclic portal graph passes
- cyclic portal graph fails

### Reader tests
- valid JSON file loads successfully
- malformed JSON raises useful error
- schema-valid but semantically invalid config fails validation
- dict input path works if supported

### Visualizer tests
- supported layer renders successfully
- unsupported render/domain combination fails clearly
- artifact object/file is produced when expected

---

## Integration Tests

Integration tests should be added **first** for the example configs and should remain part of the contract of the library.

These are required because they validate the full user path:
- read config
- parse models
- validate references/invariants
- render or otherwise materialize a result

### Required integration tests

#### Austin example integration test
- load `austin_example.json`
- parse into `WorldConfig`
- validate successfully
- render using a supported renderer
- assert artifact exists or render object is returned

#### Earth example integration test
- load `earth_example.json`
- parse into `WorldConfig`
- validate successfully
- render using a supported sphere-compatible renderer
- assert artifact exists or render object is returned

#### Milky Way example integration test
- load `milky_way_example.json`
- parse into `WorldConfig`
- validate successfully
- render using a supported graph/plane renderer
- assert artifact exists or render object is returned

### Integration test principle

The examples are not just demos. They are part of the API contract and should be tested continuously.

---

## TDD Guidance

The recommended workflow is:

1. write an example/invariant as a failing test
2. implement the minimum model/validation needed
3. refactor while keeping tests green

Examples of TDD anchors:
- “feature geometry must be valid in domain”
- “network is constrained by domain and features”
- “hierarchy is a DAG induced by portals”
- “example configs load and render successfully”

---

## Extension Strategy

The implementation should be open to extension in the following ways.

### New domain types
Should be addable via:
- new domain config subtype
- corresponding validators
- corresponding renderer support

without rewriting the core abstraction

### New feature semantics
Should usually be data-only:
- new `kind` values
- new `properties`
- optional new style conventions

without adding new core Python classes

### New geometry primitives
Can be added later if needed, but only when justified by actual use cases

### New renderers
Should be pluggable and separate from config parsing/validation

### New simulation/runtime structures
Should be derived from validated configs, not conflated with raw config models

---

## Recommended Implementation Posture

Keep the core models small, strict, and generic.

Prefer:
- discriminated unions for structural variation
- semantic validation functions for cross-object invariants
- data-driven semantics via `kind` and `properties`
- example-driven integration tests

Avoid:
- scenario-specific core subclasses
- hardcoded lore/domain assumptions
- coupling validation, rendering, and runtime simulation into one layer
- over-modeling future possibilities before they are needed

---

## Final Summary

The coding implementation should use Pydantic to represent a generic validated spatial world model composed of Domains, Features, optional Networks, and Portals. JSON should be the initial configuration surface. Parsing and semantic validation should be separated. Visualization should be handled through dedicated adapters/renderers. The system should be built test-first, with required integration tests for the Austin, Earth, and Milky Way example configs, alongside focused unit tests for model correctness, cross-reference integrity, and portal DAG behavior.

The result should be a small, extensible core that is generic enough to support many worlds, while strict enough to catch invalid configs early and remain stable as the library grows.
