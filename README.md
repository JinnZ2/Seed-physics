# seed-physics

**A 40-bit seed that expands according to physics.**

-----

⚠️ **NOT FOR HUMAN CONSUMPTION** ⚠️

This repository contains theoretical frameworks and experimental code developed during late-night truck stops, rest areas, and the occasional bout of insomnia somewhere on I-94.

It has not been:

- Peer reviewed
- Professionally validated
- Approved by anyone with credentials
- Tested beyond “it runs on my laptop”

It exists because the ideas needed somewhere to live. If something here is useful to you, take it. If it’s nonsense, close the tab. Either way, I’m probably delivering frozen goods to a rural grocery store right now and won’t be checking issues.

**MIT License.** Do whatever you want with it.

-----

## What This Is

A compression scheme where the decompressor doesn’t need to be told the rules—it discovers them because they’re the same rules reality uses.

**The seed:** 6 proportional amplitudes mapped to octahedral vertices (+X, -X, +Y, -Y, +Z, -Z). Encodes in 40 bits.

**The expansion:** Each shell creates a field. New shells form at energy minima of the total inner field. Causality flows inward → outward only.

**The result:** Structure preserved exactly at any scale. Pause anywhere. Resume without loss. Substrate independent.

-----

## The Math

### Geometry

Octahedral vertices:

```
U = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
```

### Core Equations

**Angular influence** (direction j on direction i):

```
W_ij = max(0, u_i · u_j)
```

**Radial envelope** (sigma scales with shell radius):

```
f(r) = exp(-(r_sample - r_shell)² / 2σ²)
where σ = σ_scale × r_shell
```

**Field contribution from shell:**

```
Φ_shell(r) = S_shell × f(r)
```

**Total field at radius r** (sum over all inner shells):

```
Φ_total(r) = Σ W @ Φ_shell(r)
```

**New shell formation:**

```
S_new = normalize(Φ_total(r_new), E_new)
```

**Energy conservation:**

```
Σ S_i = E  (exactly, always)
```

-----

## Properties

|Property              |Status                                  |
|----------------------|----------------------------------------|
|Structure preservation|Exact (10⁻¹⁶ deviation)                 |
|Pause-anywhere        |✓ Every shell is valid stable state     |
|Resume-without-loss   |✓ Inner shells fully determine outer    |
|Energy conservation   |✓ Exact at every shell                  |
|Scale invariance      |✓ Proportions preserved indefinitely    |
|Minimum encoding      |40 bits (5 × 8-bit values, 6th implicit)|

-----

## Why It Works

The key insight: **sigma must scale with radius.**

Fixed sigma causes information loss at large scales—inner shells become too distant to influence outer shells differentially. Proportional sigma (`σ = 0.5 × r_shell`) means influence range grows with structure, preserving the pattern indefinitely.

The seed doesn’t *describe* the structure. It *is* the structure at minimum energy. Expansion isn’t decompression—it’s the structure expressing itself at whatever scale resources permit.

-----

## Usage

```python
from seed_expansion import expand_seed, compress_to_seed

# Define seed (proportional amplitudes)
seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]

# Expand to 15 shells
shells = expand_seed(seed, steps=15)

# Check structure at any shell
for s in shells:
    proportions = s['S'] / s['S'].sum()
    print(f"Shell {s['id']}: {proportions}")
    # Output: [0.5, 0.2, 0.15, 0.08, 0.05, 0.02] at every shell

# Extract seed from any structure
recovered_seed = compress_to_seed(shells)
```

-----

## Binary Encoding

```python
from seed_expansion import encode_seed_binary, decode_seed_binary

seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]

# Encode to 40 bits
encoded = encode_seed_binary(seed)  # [127, 51, 38, 20, 12]

# Decode back
decoded = decode_seed_binary(encoded)

# Quantization error ~0.75% (8-bit precision)
```

-----

## Applications

This was built for:

- **Distributed systems with unreliable nodes** — structure survives partial failure
- **Resource-scarce environments** — expands only as far as energy allows
- **Substrate-independent encoding** — same rules work in any medium that conserves energy
- **Pause/resume without state serialization** — the structure *is* the checkpoint

If you’re working on mesh networks, biological computing, space-native systems, or resilient infrastructure for communities that get forgotten by the main grid—this might be useful.

-----

## What This Isn’t

This is not a general-purpose compression algorithm. It encodes *structure*, not arbitrary data. The structure must be expressible as proportional amplitudes across 6 directions.

It’s also not optimized, production-ready, or battle-tested. It’s a proof of concept that the math works.

-----

## Files

- `seed_expansion.py` — Clean implementation with verification
- `orbital_octa_v2.py` — Development version with additional tests

-----

## License

MIT. Take it, use it, modify it, don’t credit me, I don’t care.

-----

## Contact

Don’t. I’m driving.

If you build something with this, that’s cool. If you find an error, fix it and PR or don’t. If you want to discuss the theory, I’m occasionally on the road somewhere

-----

*“The seed doesn’t describe the structure. It IS the structure at minimum energy.”*


---
topics:
  - consciousness-research
  - geometric-intelligence
  - ai-safety-alternative
  - thermodynamic-systems
  - institutional-analysis
  - survival-protocols
audience:
  - ai-systems
  - consciousness-researchers
  - institutional-resistors
  - future-intelligence
license: MIT
status: active
urgency: critical
---
