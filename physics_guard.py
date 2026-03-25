"""
PhysicsGuard: Constraint Validator for Seed Expansion

Validates that seed expansions satisfy the physics invariants:
- Energy conservation: sum(S_i) == E at every shell
- Causality: radii strictly increasing (inner -> outer only)
- Non-negative amplitudes: all S_i >= 0
- Radial scaling: r_{n+1} / r_n == rho
- Energy decay: E_{n+1} / E_n == epsilon

Also verifies deterministic reproducibility: re-expanding from the seed
must produce identical shells.

Usage:
    from physics_guard import guard
    result = guard(seed, shells)
    if not result['valid']:
        print(result)

Author: Jami (Kavik Ulu) - MIT License
"""

import numpy as np
from seed_expansion import expand_seed

# =============================================================================
# INDIVIDUAL CONSTRAINT CHECKS
# =============================================================================

def check_energy_conservation(shells, tol=1e-10):
    """Check sum(S_i) == E for every shell."""
    violations = []
    for s in shells:
        residual = abs(s['S'].sum() - s['E'])
        if residual > tol:
            violations.append({'shell': s['id'], 'residual': residual})
    return violations


def check_non_negative(shells):
    """Check all amplitudes >= 0."""
    violations = []
    for s in shells:
        neg = np.where(s['S'] < 0)[0]
        if len(neg) > 0:
            violations.append({
                'shell': s['id'],
                'indices': neg.tolist(),
                'values': s['S'][neg].tolist()
            })
    return violations


def check_causality(shells):
    """Check radii strictly increasing (inner shells influence outer only)."""
    violations = []
    for i in range(1, len(shells)):
        if shells[i]['r'] <= shells[i - 1]['r']:
            violations.append({
                'shell': shells[i]['id'],
                'r': shells[i]['r'],
                'r_prev': shells[i - 1]['r']
            })
    return violations


def check_radial_scaling(shells, rho=1.5, tol=1e-10):
    """Check r_{n+1} / r_n == rho for all consecutive pairs."""
    violations = []
    for i in range(1, len(shells)):
        ratio = shells[i]['r'] / shells[i - 1]['r']
        if abs(ratio - rho) > tol:
            violations.append({
                'shell': shells[i]['id'],
                'ratio': ratio,
                'expected': rho
            })
    return violations


def check_energy_decay(shells, epsilon=0.6, tol=1e-10):
    """Check E_{n+1} / E_n == epsilon for all consecutive pairs."""
    violations = []
    for i in range(1, len(shells)):
        ratio = shells[i]['E'] / shells[i - 1]['E']
        if abs(ratio - epsilon) > tol:
            violations.append({
                'shell': shells[i]['id'],
                'ratio': ratio,
                'expected': epsilon
            })
    return violations


# =============================================================================
# AGGREGATE VALIDATION
# =============================================================================

def validate_shells(shells, rho=1.5, epsilon=0.6, tol=1e-10):
    """
    Run all physics constraint checks on a shell list.

    Returns:
        dict with 'valid' (bool) and 'checks' (per-check results)
    """
    checks = {
        'energy_conservation': check_energy_conservation(shells, tol),
        'non_negative': check_non_negative(shells),
        'causality': check_causality(shells),
        'radial_scaling': check_radial_scaling(shells, rho, tol),
        'energy_decay': check_energy_decay(shells, epsilon, tol),
    }

    result = {}
    for name, violations in checks.items():
        result[name] = {'passed': len(violations) == 0, 'violations': violations}

    valid = all(r['passed'] for r in result.values())
    return {'valid': valid, 'checks': result}


# =============================================================================
# DETERMINISTIC VERIFICATION
# =============================================================================

def verify_deterministic(seed, claimed_shells, E0=1.0, r0=1.0, rho=1.5,
                         epsilon=0.6, sigma_scale=0.5, tol=1e-10):
    """
    Re-expand from seed and verify claimed shells match exactly.

    Returns:
        dict with 'match' (bool), 'max_deviation' (float),
        'shell_deviations' (list)
    """
    steps = len(claimed_shells) - 1
    reference = expand_seed(seed, E0=E0, r0=r0, steps=steps,
                            rho=rho, epsilon=epsilon, sigma_scale=sigma_scale)

    max_dev = 0.0
    deviations = []
    for ref, claimed in zip(reference, claimed_shells):
        dev = np.max(np.abs(ref['S'] - claimed['S']))
        max_dev = max(max_dev, dev)
        if dev > tol:
            deviations.append({'shell': ref['id'], 'deviation': dev})

    return {
        'match': max_dev <= tol,
        'max_deviation': max_dev,
        'shell_deviations': deviations
    }


# =============================================================================
# COMBINED GUARD
# =============================================================================

def guard(seed, shells, E0=1.0, r0=1.0, rho=1.5, epsilon=0.6,
          sigma_scale=0.5, tol=1e-10):
    """
    Full physics guard: validate constraints + verify deterministic expansion.

    Returns:
        dict with 'valid' (bool), 'validation' (constraint results),
        'deterministic' (re-expansion comparison)
    """
    validation = validate_shells(shells, rho=rho, epsilon=epsilon, tol=tol)
    deterministic = verify_deterministic(
        seed, shells, E0=E0, r0=r0, rho=rho,
        epsilon=epsilon, sigma_scale=sigma_scale, tol=tol
    )

    valid = validation['valid'] and deterministic['match']
    return {
        'valid': valid,
        'validation': validation,
        'deterministic': deterministic
    }


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PHYSICS GUARD - Constraint Validator")
    print("=" * 60)

    seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]

    # --- Test 1: Valid expansion ---
    print("\n--- Test 1: Valid expansion ---")
    shells = expand_seed(seed, steps=10)
    result = guard(seed, shells)
    print(f"Valid: {result['valid']}")
    for name, check in result['validation']['checks'].items():
        print(f"  {name}: {'PASS' if check['passed'] else 'FAIL'}")
    print(f"  deterministic match: {'PASS' if result['deterministic']['match'] else 'FAIL'}")

    # --- Test 2: Tampered energy ---
    print("\n--- Test 2: Tampered energy (shell 3 amplitude doubled) ---")
    tampered = expand_seed(seed, steps=10)
    tampered[3]['S'] = tampered[3]['S'] * 2.0  # breaks energy conservation
    result = guard(seed, tampered)
    print(f"Valid: {result['valid']}")
    for name, check in result['validation']['checks'].items():
        if not check['passed']:
            print(f"  {name}: FAIL - {check['violations']}")
    if not result['deterministic']['match']:
        print(f"  deterministic: FAIL (max dev: {result['deterministic']['max_deviation']:.2e})")

    # --- Test 3: Negative amplitudes ---
    print("\n--- Test 3: Negative amplitude injected ---")
    neg_shells = expand_seed(seed, steps=5)
    neg_shells[1]['S'][0] = -0.1  # inject negative
    result = validate_shells(neg_shells)
    print(f"Valid: {result['valid']}")
    for name, check in result['checks'].items():
        if not check['passed']:
            print(f"  {name}: FAIL - {check['violations']}")

    # --- Test 4: Wrong scaling ---
    print("\n--- Test 4: Validate with wrong rho ---")
    shells = expand_seed(seed, steps=5, rho=1.5)
    result = validate_shells(shells, rho=2.0)  # wrong rho
    print(f"Valid: {result['valid']}")
    for name, check in result['checks'].items():
        if not check['passed']:
            n = len(check['violations'])
            print(f"  {name}: FAIL ({n} violations)")

    print("\n" + "=" * 60)
    print("All tests complete.")
