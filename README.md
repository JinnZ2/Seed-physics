# seed-physics

**A 40-bit seed that expands according to physics.**

A compression scheme where the decompressor doesn't need to be told the rules — it discovers them because they're the same rules reality uses.

---

## Quick Start

```bash
pip install numpy
python seed_expansion.py
```

```python
from seed_expansion import expand_seed, compress_to_seed

seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]
shells = expand_seed(seed, steps=15)

for s in shells:
    proportions = s['S'] / s['S'].sum()
    print(f"Shell {s['id']}: {proportions}")
    # Output: [0.5, 0.2, 0.15, 0.08, 0.05, 0.02] at every shell
```

---

## How It Works

**The seed:** 6 proportional amplitudes mapped to octahedral vertices (+X, -X, +Y, -Y, +Z, -Z). Encodes in 40 bits.

**The expansion:** Each shell creates a field. New shells form at energy minima of the total inner field. Causality flows inward to outward only.

**The result:** Structure preserved exactly at any scale. Pause anywhere. Resume without loss. Substrate independent.

The key insight: **sigma must scale with radius.** Fixed sigma causes information loss at large scales — inner shells become too distant to influence outer shells differentially. Proportional sigma (`sigma = 0.5 * r_shell`) means influence range grows with structure, preserving the pattern indefinitely.

The seed doesn't *describe* the structure. It *is* the structure at minimum energy.

---

## The Math

### Geometry

Octahedral vertices:

```
U = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
```

### Core Equations

**Angular influence** (direction j on direction i):
```
W_ij = max(0, u_i . u_j)
```

**Radial envelope** (sigma scales with shell radius):
```
f(r) = exp(-(r_sample - r_shell)^2 / 2*sigma^2)
where sigma = sigma_scale * r_shell
```

**Field contribution from shell:**
```
Phi_shell(r) = S_shell * f(r)
```

**Total field at radius r** (sum over all inner shells):
```
Phi_total(r) = sum( W @ Phi_shell(r) )
```

**New shell formation:**
```
S_new = normalize(Phi_total(r_new), E_new)
```

**Energy conservation:**
```
sum(S_i) = E  (exactly, always)
```

---

## Properties

| Property | Status |
|---|---|
| Structure preservation | Exact (10^-16 deviation) |
| Pause-anywhere | Every shell is a valid stable state |
| Resume-without-loss | Inner shells fully determine outer |
| Energy conservation | Exact at every shell |
| Scale invariance | Proportions preserved indefinitely |
| Minimum encoding | 40 bits (5x8-bit values, 6th implicit) |

---

## Binary Encoding

```python
from seed_expansion import encode_seed_binary, decode_seed_binary

seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]
encoded = encode_seed_binary(seed)   # [127, 51, 38, 20, 12]
decoded = decode_seed_binary(encoded)
# Quantization error ~0.75% (8-bit precision)
```

---

## Modules

### Core

| Module | Description |
|---|---|
| `seed_expansion.py` | Primary implementation. Deterministic expansion, binary encoding, verification |
| `orbital_octa_v2.py` | Extended implementation with tunable sharpness and test suite |
| `seed_exploration.py` | Adaptive growth with complexity-based mode switching |

### Protocol

| Module | Description |
|---|---|
| `seed_protocol.py` | v1 transport: 13-byte packets with CRC16 for degraded networks |
| `seed_protocol_v2.py` | v2 transport: 21-byte packets with spatial position encoding |

### Network

| Module | Description |
|---|---|
| `seed_udp.py` | Simple UDP broadcast/receive for seed discovery |
| `seed_mesh_sim.py` | In-process multi-node simulation (40 nodes) with routing |
| `seed_mesh_udp.py` | Real UDP mesh on localhost with packet loss and jitter |
| `seed_mesh_lan.py` | Multi-machine LAN mesh via IP multicast |

---

## Running

```bash
# Core demos
python seed_expansion.py
python orbital_octa_v2.py
python seed_exploration.py

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

---

## Applications

- **Distributed systems with unreliable nodes** — structure survives partial failure
- **Resource-scarce environments** — expands only as far as energy allows
- **Substrate-independent encoding** — same rules work in any medium that conserves energy
- **Pause/resume without state serialization** — the structure *is* the checkpoint
- **Mesh networking** — seeds converge into spatial clusters via field coupling

---

## Ecosystem

This repo is part of a broader protocol ecosystem:

- **[TRDAP](https://github.com/JinnZ2/TRDAP)** — Carries Seed Protocol reference implementations (v1-v4), mesh transport layers, and deployment guides

Connections are declared in `.fieldlink`. The repo works standalone with `numpy` only.

---

## Contributing

Issues, PRs, and forks are welcome. If you find a bug, fix it and PR. If you want to extend the protocol, check `CLAUDE.md` for architecture and naming conventions.

**Physics constraints any contribution must respect:**
- Causality: only inner shells influence outer shells
- Energy conservation: `sum(S_i) = E` exactly at every shell
- Scale invariance: `sigma = sigma_scale * r_shell`
- Non-negative amplitudes: all `S_i >= 0`

---

## Origin

This started at truck stops and rest areas on I-94 — late nights, long hauls, and the kind of thinking that happens when the road is empty and the math won't leave you alone. The ideas needed somewhere to live. Now they do.

---

## License

MIT. Use it, modify it, build on it.

---

*"The seed doesn't describe the structure. It IS the structure at minimum energy."*
