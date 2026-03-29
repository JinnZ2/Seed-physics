# Seed Physics - Development Guide

## Project Overview

Physics-compliant seed expansion: a 40-bit seed encodes 6 proportional amplitudes across octahedral vertices, expanding deterministically via energy conservation and field-mediated coupling. Any compliant decompressor reproduces identical structure.

## Architecture

### Core Modules

- **`seed_expansion.py`** - Primary implementation. Deterministic expansion preserving seed structure exactly. Contains: `angular_weight`, `radial_envelope`, `field_contribution`, `total_field`, `normalize_to_energy`, `build_influence_matrix`, `form_shell`, `expand_seed`, binary encoding/decoding, verification.

- **`orbital_octa_v2.py`** - Extended implementation with tunable `sharpness` parameter for angular focus control. Adds test suite covering: influence matrix properties, causality, pause/resume, seed preservation, energy conservation, sharpness effects. Uses standardized function names matching `seed_expansion.py`.

- **`seed_exploration.py`** - Adaptive growth extension. Imports from `seed_expansion`. Adds: complexity-based mode switching (explore vs expand), dynamic sigma, saturation, resonance fields, pruning, Shannon entropy cost analysis.

### Protocol Modules

- **`seed_protocol.py`** - v1 transport layer. 13-byte packets with CRC16 for degraded networks. Encodes seed + energy hint + epoch. Includes minimal deterministic expansion core.

- **`seed_protocol_v2.py`** - v2 transport with spatial coupling. 21-byte packets adding position encoding (anchor cell + local offset) and neighbor routing hints.

### Validation Modules

- **`physics_guard.py`** - Constraint validator for seed expansions. Checks energy conservation, causality, non-negative amplitudes, radial scaling, and energy decay. Re-expands from seed to verify deterministic reproducibility. Single entry point: `guard(seed, shells)`.

### Agent Modules

- **`constraint_agent.py`** - Seed-native agent with bloom/explore/compress lifecycle. Uses exact-rational arithmetic (fractions) for energy accounting. Expands outward from a seed ID, traverses discovered constraint geometry, collapses back preserving the geometric map. Serializable. Extension hooks for Rosetta, Mandala, and Emotions-as-Sensors integration.

### Network Modules

- **`seed_udp.py`** - Simple UDP broadcast/receive. Sends seed packets at 1Hz, receiver reconstructs shells from incoming seeds. Designed for lossy/intermittent networks.

- **`seed_mesh_sim.py`** - In-process multi-node simulation (40 nodes). Demonstrates seed convergence, spatial clustering, and gradient-based routing without real networking.

- **`seed_mesh_udp.py`** - Real UDP mesh on localhost. Range-limited communication with packet loss and jitter simulation. Nodes converge seeds and positions.

- **`seed_mesh_lan.py`** - Multi-machine LAN mesh via IP multicast (224.1.1.1). No hardcoded peers — automatic discovery via multicast group.

### Shared Conventions

- **Function names**: `angular_weight`, `field_contribution`, `total_field`, `form_shell`, `expand_seed`, `normalize_to_energy`, `build_influence_matrix`
- **Parameter names**: `sigma_scale` (radial influence width as fraction of shell radius), `rho` (radial scaling), `epsilon` (energy decay), `E0` (initial energy), `r0` (initial radius)
- **Shell format**: `{'id': int, 'r': float, 'E': float, 'S': np.array(6)}`
- **Geometry constant**: `U` - 6x3 array of octahedral vertex unit vectors

### Dependency Flow

```
seed_exploration.py
    -> imports from seed_expansion.py

seed_udp.py
    -> imports from seed_protocol.py

seed_mesh_sim.py
    -> imports from seed_protocol_v2.py

physics_guard.py
    -> imports from seed_expansion.py

constraint_agent.py
    (standalone, no numpy dependency — stdlib only: fractions, dataclasses, enum)

orbital_octa_v2.py
    (standalone, parallel implementation with sharpness)

seed_expansion.py, seed_protocol.py, seed_protocol_v2.py
    -> imports: numpy only (+ struct, zlib for protocol modules)

seed_mesh_udp.py, seed_mesh_lan.py
    (standalone, self-contained networking)
```

## Running

```bash
# Requires numpy
pip install numpy

# Core demos
python seed_expansion.py
python orbital_octa_v2.py
python seed_exploration.py
python physics_guard.py
python constraint_agent.py

# Protocol demos
python seed_protocol.py
python seed_protocol_v2.py

# Network demos
python seed_mesh_sim.py            # in-process simulation
python seed_udp.py send            # broadcast seeds
python seed_udp.py recv            # receive and reconstruct
python seed_mesh_udp.py            # localhost UDP mesh
python seed_mesh_lan.py            # LAN multicast mesh
```

## Key Physics Constraints

- **Causality**: Only inner shells influence outer shells (r < r_sample)
- **Energy conservation**: Sum(S_i) = E exactly at every shell
- **Scale invariance**: sigma = sigma_scale * r_shell (influence range proportional to radius)
- **Non-negative amplitudes**: All S_i >= 0

## Protocol Constraints

- **Deterministic expansion**: `expand_seed(seed)` must produce identical results everywhere
- **Stateless reconstruction**: Seed alone is sufficient to rebuild full structure
- **Identity**: `seed_distance(a, b) < threshold` defines same-entity relationship
- **Packet sizes**: v1 = 13 bytes, v2 = 21 bytes (radio-safe)

## Network Behavior

- Seeds converge into local clusters via field coupling
- Nodes physically drift toward similar seeds
- Routing emerges via gradient descent in seed-space
- Recovery after outage requires only the seed (no external state)

## Fieldlink

The `.fieldlink` file declares this repo's bidirectional API surface:

- **`provides`** — All modules and their exported functions, organized by layer (physics, protocol, transport, mesh)
- **`consumes`** — External modules this repo can integrate with for extended functionality (agent framework, visualization, persistence, crypto)
- **`interfaces`** — Shared data formats (seed vectors, shell dicts, packets, geometry)
- **`hooks`** — Callback points for ecosystem integration (on_seed_received, on_shell_formed, on_mode_switch, on_node_update)
- **`constraints`** — Physics invariants that any consumer/provider must respect

The repo works standalone with `numpy` only. When connected to an ecosystem, the `consumes` section declares what it can use and the `hooks` section declares where external code can attach.

## Naming Conventions

- Files: `snake_case.py`
- Functions: `snake_case`
- Constants: `UPPER_CASE` or single uppercase letter (`U`, `E0`)
- Parameters: `snake_case` (`sigma_scale`, `r_shell`, `E_new`)

## Design Notes

### Planned: seed_agent_tcp.py

TCP-based seed agents that exchange SeedPackets instead of strings. Depends on external `core.Agent` and `transports.TCPTransport` (not yet implemented). Design:
- Agents reconstruct local field from received seeds
- Identity + sync derived from seed similarity
- Mesh propagation via broadcast_seed()

### Multiagent Field Superposition

Multiple seeds combine into shared fields:
- `combine_seeds(seeds)` averages and normalizes
- Routing = gradient descent in seed-space (packet moves "downhill")
- Clusters form spatially with similar seeds
- Network converges without central coordination

### Spatial Coupling Cost Function

```
J = alpha * D_seed(S_i, S_j) + beta * D_space(x_i, x_j) + gamma * delta_E
```

Where:
- D_seed = L1 or cosine distance in 6D
- D_space = Euclidean distance
- delta_E = energy mismatch penalty

Drives: similar seeds -> move closer, dissimilar seeds -> separate.
