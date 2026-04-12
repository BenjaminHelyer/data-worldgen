# Spatial Data Implementation Plan (v0)

This plan operationalizes `SPATIAL_DATA_OVERVIEW.md` into an implementation sequence
that minimizes lock-in while still delivering one complete vertical slice.

## Candidate first vertical slices

1. **City on flat 2D (recommended first)**
   - Domain: plane (bounded)
   - Features: roads and blocks
   - Network: road intersection graph
   - Why first: easiest geometry and strongest testability.

2. **Galaxy as graph**
   - Domain: abstract graph metric
   - Features: star systems/sectors
   - Network: hyperlanes
   - Why second: simpler topology, weaker geometry pressure.

3. **Planet on sphere**
   - Domain: sphere with geodesic assumptions
   - Features: cities/regions
   - Network: long-distance routes
   - Why later: introduces spherical geometry complexity.

## Architectural decisions made for v0

- **Pydantic-first contract** for domain/network/feature/layer/world schemas.
- **Geometry and topology remain independent** in model shape, but linked by validation.
- **Keep coordinates generic** (list of points) before introducing specialized geometry libs.
- **Start deterministic generation** to enable reliable tests and CI stability.
- **Visualization utility with matplotlib** for immediate sanity checks and demos.

## Proposed implementation order

1. Core models (`Domain`, `Feature`, `Network`, `Layer`, `World`, `Portal`)
2. First generator: flat city with road grid + block polygons + directed road graph
3. Plotting utility for layers
4. Tests for schema constraints and end-to-end city generation
5. Follow-up: spherical planet and galaxy graph adapters

## Forward-compatibility notes

- When we add `sphere_2d`, coordinate semantics should be explicit (lat/lon vs 3D unit vector).
- Keep `properties` dictionaries for extensibility, but stabilize core key names via docs.
- Future optional dependency: networkx/shapely only when needed, not in v0.
- Portal mappings will eventually need richer references (feature subsets, transform metadata).
