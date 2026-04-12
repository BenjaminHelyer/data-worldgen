# SPATIAL_DATA_OVERVIEW.md

## Overview

This document defines a unified spatial abstraction for modeling worlds across multiple scales—from galaxies down to individual rooms. The goal is to support both **simulation** (agents moving through space) and **visualization** (maps, layouts, game environments) in a single coherent framework.

The system separates three fundamental concerns:

- **Geometry**: what space exists  
- **Topology**: how things connect or can be traversed  
- **Hierarchy**: how spaces relate across scales  

---

## Core Abstraction

World = (L, P)

- L = set of Layers  
- P = set of Portals  

Each Layer is defined as:

Layer = (Domain, Features, Network)

---

## Three Fundamental Concepts

Geometry  = Domain + Features  
Topology  = Network  
Hierarchy = Portals (DAG over Layers)

These concepts are **independent but composable**.

---

## Domain (Geometry Foundation)

Domain = (X, d)

- X = underlying space  
- d = metric: X × X → ℝ≥0  

In implementation terms:

> A Domain is a metric space optionally equipped with an atlas (coordinate charts).

### Examples

- Plane → ℝ² with Euclidean metric  
- Sphere → S² with geodesic metric  
- Interior space → subset of ℝ² with walls/holes  
- Abstract graph → shortest-path metric  

---

## Features (Embedded Structure)

Feature ⊂ X

Feature = (kind, geometry ⊂ X, properties, style?)

- **kind**: semantic meaning (building, road, room, etc.)
- **geometry**: point, path, or region embedded in Domain
- **properties**: metadata
- **style**: optional rendering hint

### Constraint

- geometry must be valid within the Domain

### Examples

- A city → point on a sphere  
- A road → path in ℝ²  
- A room → polygon in ℝ²  
- A wall → line segment acting as barrier  

---

## Network (Topology)

Network = (V, E, w)

- V = nodes  
- E = edges  
- w = edge attributes / costs  

### Constraint

Network ⊆ feasible paths induced by (Domain, Features)

### Interpretation

- Domain + Features define **what is physically possible**
- Network defines **what is allowed or modeled for traversal**

### Examples

- Road network in a city  
- Pedestrian navigation graph inside a building  
- Hyperlane graph between planets  

---

## Portals (Hierarchy)

Portal: U ⊆ X_A → V ⊆ X_B

A Portal is a **local mapping between subsets of Domains**.

### Induced Structure

Hierarchy = directed acyclic graph (DAG) over Layers

### Constraints

- mappings are local (subset → subset)
- no cycles
- multiple parents (fan-in) allowed

### Examples

- Door: room → hallway  
- City node → detailed city layer  
- Planet point → planetary surface layer  

---

## Putting It Together

Each Layer can emphasize different aspects:

- Geometry-heavy: interiors, buildings  
- Topology-heavy: galaxy maps  
- Mixed: cities, planets  

This flexibility allows the system to represent:

- continuous spaces (rooms, terrain)
- discrete structures (graphs, networks)
- multiscale worlds (galaxy → room)

---

## Worked Examples

### Example 1: Galaxy → Planet → City

Layer: Galaxy  
- Domain: plane  
- Features: planets (points), sectors (regions)  
- Network: hyperlanes  
- Portals: planet → planet surface  

Layer: Planet  
- Domain: sphere  
- Features: cities, regions  
- Network: travel routes  
- Portals: city → city layer  

Layer: City  
- Domain: plane  
- Features: districts, roads, buildings  
- Network: pedestrian/vehicle graph  
- Portals: building → interior  

---

### Example 2: House Interior

Layer: HouseInterior  
- Domain: subset of ℝ²  
- Features:
  - rooms (regions)
  - walls (barriers)
  - doors (connections)
  - furniture (points/regions)
- Network: optional navigation graph  

This is a **geometry-first layer**, where movement can be continuous.

---

## Final Summary

Layer = (Domain: metric space,  
         Features: subsets of Domain,  
         Network?: constrained traversal)

World = DAG of Layers via Portals  
