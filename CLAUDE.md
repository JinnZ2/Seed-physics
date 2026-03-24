# Seed Physics - Development Guide

## Project Overview

Physics-compliant seed expansion: a 40-bit seed encodes 6 proportional amplitudes across octahedral vertices, expanding deterministically via energy conservation and field-mediated coupling. Any compliant decompressor reproduces identical structure.

## Architecture

### Core Modules

- **`seed_expansion.py`** - Primary implementation. Deterministic expansion preserving seed structure exactly. Contains: `angular_weight`, `radial_envelope`, `field_contribution`, `total_field`, `normalize_to_energy`, `build_influence_matrix`, `form_shell`, `expand_seed`, binary encoding/decoding, verification.

- **`orbital_octa_v2.py`** - Extended implementation with tunable `sharpness` parameter for angular focus control. Adds test suite covering: influence matrix properties, causality, pause/resume, seed preservation, energy conservation, sharpness effects. Uses standardized function names matching `seed_expansion.py`.

- **`seed_exploration.py`** - Adaptive growth extension. Imports from `seed_expansion`. Adds: complexity-based mode switching (explore vs expand), dynamic sigma, saturation, resonance fields, pruning, Shannon entropy cost analysis.

### Shared Conventions

- **Function names**: `angular_weight`, `field_contribution`, `total_field`, `form_shell`, `expand_seed`, `normalize_to_energy`, `build_influence_matrix`
- **Parameter names**: `sigma_scale` (radial influence width as fraction of shell radius), `rho` (radial scaling), `epsilon` (energy decay), `E0` (initial energy), `r0` (initial radius)
- **Shell format**: `{'id': int, 'r': float, 'E': float, 'S': np.array(6)}`
- **Geometry constant**: `U` - 6x3 array of octahedral vertex unit vectors

### Dependency Flow

```
seed_exploration.py
    -> imports from seed_expansion.py

orbital_octa_v2.py
    (standalone, parallel implementation with sharpness)

seed_expansion.py
    -> imports: numpy only
```

## Running

```bash
# Requires numpy
pip install numpy

# Run demos
python seed_expansion.py
python orbital_octa_v2.py
python seed_exploration.py
```

## Key Physics Constraints

- **Causality**: Only inner shells influence outer shells (r < r_sample)
- **Energy conservation**: Sum(S_i) = E exactly at every shell
- **Scale invariance**: sigma = sigma_scale * r_shell (influence range proportional to radius)
- **Non-negative amplitudes**: All S_i >= 0

## Naming Conventions

- Files: `snake_case.py`
- Functions: `snake_case`
- Constants: `UPPER_CASE` or single uppercase letter (`U`, `E0`)
- Parameters: `snake_case` (`sigma_scale`, `r_shell`, `E_new`)
