"""
Seed Exploration: Adaptive Growth Module
=========================================

Extension to seed_expansion.py that adds adaptive, non-linear growth
capabilities when energy is abundant.

CORE PRINCIPLE:
- expand() preserves structure exactly (the trunk)
- explore() allows adaptive variation (the branches)
- Switch between modes based on energy budget vs complexity cost

When energy is abundant:
- Adaptive sharpness: field focus responds to local density
- Saturation: prevents single-direction dominance
- Resonance: past shells weakly influence current formation

When energy is scarce:
- Falls back to deterministic expand() mode
- Structure crystallizes and preserves

The complexity cost (Shannon entropy) of the seed determines the
energy threshold for switching between modes.

Author:  (Kavik Ulu) and AI partners - MIT License
"""

import numpy as np

# Import core functions from seed_expansion
from seed_expansion import (
    U, 
    normalize_to_energy, 
    build_influence_matrix,
    field_contribution,
    radial_envelope,
    total_field,
    expand_seed
)


# =============================================================================
# COMPLEXITY COST (Information-Theoretic)
# =============================================================================

def shannon_entropy(S, eps=1e-12):
    """
    Calculate Shannon entropy H(S) of amplitude distribution.
    
    H(S) = -Σ p_i × log₂(p_i)
    
    Returns entropy in bits.
    """
    S_prop = S / (S.sum() + eps)
    S_prop = np.maximum(S_prop, eps)  # Avoid log(0)
    return -np.sum(S_prop * np.log2(S_prop))


def complexity_cost(S, H_max=2.585):
    """
    Calculate complexity cost C(S) = H_max - H(S).
    
    - Uniform distribution: C ≈ 0 (low cost, easy to maintain)
    - Highly asymmetric: C → H_max (high cost, expensive to maintain)
    
    H_max ≈ 2.585 bits for 6 states (log₂(6)).
    """
    H_S = shannon_entropy(S)
    return H_max - H_S


def branching_threshold(S, k=0.5):
    """
    Calculate energy threshold for branching.
    
    E_branch = k × C(S)
    
    When E > E_branch: explore() mode (innovation)
    When E < E_branch: expand() mode (preservation)
    """
    return k * complexity_cost(S)


# =============================================================================
# DYNAMIC PARAMETERS
# =============================================================================

def dynamic_sigma(field, sigma_min=0.1, sigma_max=0.8, gamma=2.0, phi_max=1.0):
    """
    Adaptive sharpness: sigma shrinks as field strength increases.
    
    σ_n = σ_min + (σ_max - σ_min) × exp(-γ × ||Φ||/Φ_max)
    
    High field density → sharp influence → branching
    Low field density → diffuse influence → smoothing
    """
    field_magnitude = np.linalg.norm(field)
    normalized = field_magnitude / phi_max
    sigma = sigma_min + (sigma_max - sigma_min) * np.exp(-gamma * normalized)
    return np.clip(sigma, sigma_min, sigma_max)


def dynamic_epsilon(S_prev, epsilon_max=0.95, epsilon_min=0.50, H_max=2.585):
    """
    Dynamic energy decay based on previous shell's complexity.
    
    ε_n = ε_max - (ε_max - ε_min) × C(S_{n-1})/H_max
    
    Asymmetric shells → low ε → rapid energy decay
    Symmetric shells → high ε → slow energy decay
    
    This creates self-regulating feedback:
    Asymmetry → High cost → Rapid stabilization
    """
    C_S = complexity_cost(S_prev, H_max)
    decay_range = epsilon_max - epsilon_min
    normalized_cost = C_S / H_max
    return epsilon_max - (decay_range * normalized_cost)


# =============================================================================
# EXPLORATION MECHANISMS
# =============================================================================

def resonance_field(shells, alpha=0.05, beta=0.25):
    """
    Calculate resonance contribution from all inner shells.
    
    Resonance_n = Σ α × V_i × exp(-β × (n-i))
    
    Where V_i = S_i/||S_i|| - 1/6 (deviation from uniform)
    
    Past shell structure weakly influences current formation,
    creating long-range correlations.
    """
    n = len(shells)
    resonance = np.zeros(6)
    
    for i, shell in enumerate(shells):
        S_prop = shell['S'] / shell['S'].sum()
        V_i = S_prop - (1/6)  # Deviation from uniform
        
        decay = np.exp(-beta * (n - i))
        resonance += alpha * V_i * decay
    
    return resonance


def saturate(field, kappa=5.0):
    """
    Apply saturation to prevent single-direction dominance.
    
    S_saturated = tanh(κ × Φ)
    
    For small values: tanh(x) ≈ x (linear response)
    For large values: tanh(x) → 1 (saturation)
    
    This forces more equitable energy distribution.
    """
    return np.tanh(kappa * field)


def efficiency_stress(S, H_max=2.585):
    """
    Calculate efficiency stress for each direction.
    
    Stress_i = C(p_i) × |p_i - 1/6|
    
    High stress = direction is costly to maintain.
    Used for pruning inefficient branches.
    """
    S_prop = S / S.sum()
    stress = np.zeros(6)
    
    for i in range(6):
        p_i = S_prop[i]
        # Deviation from ideal uniform state
        deviation = abs(p_i - (1/6))
        # Weight by how "extreme" this amplitude is
        if p_i > 1e-12:
            # Use -p*log(p) as complexity contribution
            C_i = -p_i * np.log2(p_i) if p_i < 1 else 0
        else:
            C_i = 0
        stress[i] = C_i * deviation
    
    return stress


def prune_and_reinvest(field_saturated, S_prev, E_new, lambda_prune=0.2):
    """
    Apply pruning based on efficiency stress, then reinvest energy.
    
    S_new = Φ_saturated - λ × Σ_stress
    
    Energy from pruned directions redistributes to efficient ones.
    """
    stress = efficiency_stress(S_prev)
    
    # Subtractive causality
    S_pruned = field_saturated - (lambda_prune * stress)
    
    # Clamp negative values and normalize
    S_pruned = np.maximum(S_pruned, 0.0)
    
    return normalize_to_energy(S_pruned, E_new)


# =============================================================================
# FIELD CALCULATION FOR EXPLORATION
# =============================================================================

def total_field_explore(shells, r_sample, W, sigma_min=0.1, sigma_max=0.8, 
                        gamma=2.0, alpha=0.05, beta=0.25):
    """
    Calculate total field with dynamic sigma and resonance.
    
    1. Compute base field with average sigma
    2. Determine dynamic sigma from field magnitude
    3. Recompute field with dynamic sigma
    4. Add resonance term
    """
    # First pass: get field magnitude with default sigma
    default_sigma = (sigma_min + sigma_max) / 2
    base_field = np.zeros(6)
    
    for shell in shells:
        if shell['r'] >= r_sample:
            continue
        contrib = field_contribution(shell['S'], shell['r'], r_sample, default_sigma)
        base_field += W @ contrib
    
    # Determine dynamic sigma
    sigma_n = dynamic_sigma(base_field, sigma_min, sigma_max, gamma)
    
    # Second pass: recompute with dynamic sigma
    field = np.zeros(6)
    for shell in shells:
        if shell['r'] >= r_sample:
            continue
        contrib = field_contribution(shell['S'], shell['r'], r_sample, sigma_n)
        field += W @ contrib
    
    # Add resonance
    field += resonance_field(shells, alpha, beta)
    
    return field


# =============================================================================
# MAIN EXPLORATION ALGORITHM
# =============================================================================

def explore_seed(seed, E0=1.0, r0=1.0, steps=10, rho=1.3, 
                 kappa=5.0, alpha=0.05, beta=0.25,
                 sigma_min=0.1, sigma_max=0.8, gamma=2.0,
                 lambda_prune=0.2, k_threshold=0.5,
                 epsilon_max=0.95, epsilon_min=0.50):
    """
    Explore seed with adaptive, non-linear growth.
    
    Parameters:
    -----------
    seed : array-like, length 6
        Initial proportional amplitudes
    E0 : float
        Initial energy budget
    r0 : float
        Initial radius
    steps : int
        Number of shells to grow
    rho : float
        Radial scaling factor
    kappa : float
        Saturation gain (higher = more dampening)
    alpha : float
        Resonance strength
    beta : float
        Resonance decay rate
    sigma_min, sigma_max : float
        Bounds for adaptive sharpness
    gamma : float
        Sharpness sensitivity to field strength
    lambda_prune : float
        Pruning sensitivity
    k_threshold : float
        Branching threshold scaling
    epsilon_max, epsilon_min : float
        Bounds for dynamic energy decay
    
    Returns:
    --------
    shells : list of dicts
        Each shell has 'id', 'r', 'E', 'S', 'mode', 'epsilon'
    """
    W = build_influence_matrix()
    
    # Initialize
    seed_arr = np.array(seed, dtype=float)
    seed_normalized = normalize_to_energy(seed_arr, E0)
    seed_proportions = seed_normalized / E0  # For expand() fallback
    
    # Calculate global branching threshold
    E_branch = branching_threshold(seed_arr, k_threshold)
    
    shells = [{
        'id': 0,
        'r': r0,
        'E': E0,
        'S': seed_normalized.copy(),
        'mode': 'SEED',
        'epsilon': None
    }]
    
    for n in range(1, steps + 1):
        r_new = rho * shells[-1]['r']
        S_prev = shells[-1]['S']
        
        # Dynamic energy decay based on previous shell's complexity
        epsilon_n = dynamic_epsilon(S_prev, epsilon_max, epsilon_min)
        E_new = epsilon_n * shells[-1]['E']
        
        # Mode decision
        if E_new > E_branch:
            # EXPLORE MODE: Adaptive, non-linear growth
            
            # Calculate field with dynamic sigma and resonance
            field = total_field_explore(
                shells, r_new, W, 
                sigma_min, sigma_max, gamma,
                alpha, beta
            )
            
            # Apply saturation
            field_saturated = saturate(field, kappa)
            
            # Prune inefficient directions and reinvest energy
            S_new = prune_and_reinvest(field_saturated, S_prev, E_new, lambda_prune)
            
            mode = 'EXPLORE'
        else:
            # EXPAND MODE: Deterministic preservation
            # Preserve seed proportions exactly
            S_new = normalize_to_energy(seed_proportions.copy(), E_new)
            mode = 'EXPAND'
        
        shells.append({
            'id': n,
            'r': r_new,
            'E': E_new,
            'S': S_new,
            'mode': mode,
            'epsilon': epsilon_n
        })
    
    return shells


def full_growth(seed, E0=1.0, r0=1.0, steps=10, **kwargs):
    """
    Convenience wrapper for explore_seed with sensible defaults.
    
    Returns shells with mode information showing where
    exploration vs expansion occurred.
    """
    return explore_seed(seed, E0, r0, steps, **kwargs)


# =============================================================================
# ANALYSIS UTILITIES
# =============================================================================

def analyze_growth(shells, seed):
    """
    Analyze growth pattern and return summary statistics.
    """
    seed_prop = np.array(seed) / np.sum(seed)
    
    results = {
        'total_shells': len(shells),
        'explore_shells': sum(1 for s in shells if s['mode'] == 'EXPLORE'),
        'expand_shells': sum(1 for s in shells if s['mode'] == 'EXPAND'),
        'switch_point': None,
        'final_deviation': None,
        'max_deviation': 0.0,
        'energy_trace': [],
        'complexity_trace': []
    }
    
    # Find switch point
    for i, s in enumerate(shells):
        if i > 0 and s['mode'] == 'EXPAND' and shells[i-1]['mode'] == 'EXPLORE':
            results['switch_point'] = i
            break
    
    # Calculate deviations and traces
    for s in shells:
        S_prop = s['S'] / s['S'].sum()
        deviation = np.max(np.abs(S_prop - seed_prop))
        results['max_deviation'] = max(results['max_deviation'], deviation)
        results['energy_trace'].append(s['E'])
        results['complexity_trace'].append(complexity_cost(s['S']))
    
    # Final deviation
    final_prop = shells[-1]['S'] / shells[-1]['S'].sum()
    results['final_deviation'] = np.max(np.abs(final_prop - seed_prop))
    
    return results


def print_growth_summary(shells, seed):
    """
    Print formatted summary of growth.
    """
    analysis = analyze_growth(shells, seed)
    seed_prop = np.array(seed) / np.sum(seed)
    
    print("="*70)
    print("GROWTH SUMMARY")
    print("="*70)
    print(f"Seed proportions: {np.round(seed_prop, 4)}")
    print(f"Seed complexity cost: {complexity_cost(np.array(seed)):.4f}")
    print(f"Branching threshold: {branching_threshold(np.array(seed)):.4f}")
    print()
    print(f"Total shells: {analysis['total_shells']}")
    print(f"Explore shells: {analysis['explore_shells']}")
    print(f"Expand shells: {analysis['expand_shells']}")
    print(f"Switch point: Shell {analysis['switch_point']}")
    print()
    print(f"Max deviation from seed: {analysis['max_deviation']:.4f}")
    print(f"Final deviation: {analysis['final_deviation']:.4f}")
    print()
    
    print("Shell-by-shell:")
    print("-"*70)
    print(f"{'Shell':>5} {'Mode':>8} {'Epsilon':>8} {'Energy':>10} {'C(S)':>8} {'Deviation':>10}")
    print("-"*70)
    
    for s in shells:
        S_prop = s['S'] / s['S'].sum()
        deviation = np.max(np.abs(S_prop - seed_prop))
        C_S = complexity_cost(s['S'])
        eps_str = f"{s['epsilon']:.4f}" if s['epsilon'] else "N/A"
        
        print(f"{s['id']:>5} {s['mode']:>8} {eps_str:>8} {s['E']:>10.6f} {C_S:>8.4f} {deviation:>10.4f}")


# =============================================================================
# VERIFICATION
# =============================================================================

def verify_exploration(seed, steps=15):
    """
    Verify exploration produces expected behavior.
    """
    print("="*70)
    print("EXPLORATION VERIFICATION")
    print("="*70)
    
    shells = explore_seed(seed, steps=steps)
    print_growth_summary(shells, seed)
    
    # Check key properties
    print()
    print("Verification checks:")
    
    # 1. Energy conservation (each shell sums to its E)
    energy_check = all(
        abs(s['S'].sum() - s['E']) < 1e-10 
        for s in shells
    )
    print(f"  Energy conservation: {'PASS' if energy_check else 'FAIL'}")
    
    # 2. Mode switching occurred
    modes = [s['mode'] for s in shells]
    has_explore = 'EXPLORE' in modes
    has_expand = 'EXPAND' in modes
    print(f"  Explore mode used: {'YES' if has_explore else 'NO'}")
    print(f"  Expand mode used: {'YES' if has_expand else 'NO'}")
    
    # 3. Deviation from seed (should be non-zero for explore shells)
    seed_prop = np.array(seed) / np.sum(seed)
    explore_deviations = []
    for s in shells:
        if s['mode'] == 'EXPLORE':
            S_prop = s['S'] / s['S'].sum()
            explore_deviations.append(np.max(np.abs(S_prop - seed_prop)))
    
    if explore_deviations:
        max_explore_dev = max(explore_deviations)
        print(f"  Max explore deviation: {max_explore_dev:.4f}")
        print(f"  Branching occurred: {'YES' if max_explore_dev > 0.01 else 'MINIMAL'}")
    
    return shells


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("SEED EXPLORATION MODULE")
    print("Adaptive Growth with Complexity-Based Mode Switching")
    print("="*70)
    
    # Test 1: Asymmetric seed (high complexity cost, early stabilization)
    print("\n" + "="*70)
    print("TEST 1: Asymmetric Seed (High Complexity Cost)")
    print("="*70)
    asymmetric_seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]
    shells_asym = verify_exploration(asymmetric_seed, steps=12)
    
    # Test 2: Near-symmetric seed (low complexity cost, extended exploration)
    print("\n" + "="*70)
    print("TEST 2: Near-Symmetric Seed (Low Complexity Cost)")
    print("="*70)
    symmetric_seed = [0.18, 0.17, 0.17, 0.16, 0.16, 0.16]
    shells_sym = verify_exploration(symmetric_seed, steps=12)
    
    # Test 3: Highly asymmetric seed (very high cost, immediate stabilization)
    print("\n" + "="*70)
    print("TEST 3: Highly Asymmetric Seed (Very High Complexity Cost)")
    print("="*70)
    extreme_seed = [0.80, 0.10, 0.05, 0.03, 0.01, 0.01]
    shells_extreme = verify_exploration(extreme_seed, steps=12)
    
    print("\n" + "="*70)
    print("INTERPRETATION")
    print("="*70)
    print("""
The exploration module demonstrates:

1. COMPLEXITY-BASED SWITCHING
   - High-cost seeds (asymmetric) stabilize early
   - Low-cost seeds (symmetric) explore longer
   - "Symmetry tends to happen" emerges from energy constraints

2. ADAPTIVE MECHANISMS
   - Dynamic sharpness: field focus responds to density
   - Saturation: prevents single-direction dominance
   - Resonance: past shells influence current formation
   - Pruning: inefficient directions shed energy to efficient ones

3. SELF-REGULATION
   - Asymmetry is metabolically expensive
   - High cost → rapid energy decay → early stabilization
   - The system naturally tends toward lower-energy configurations

4. TWO-PHASE LIFECYCLE
   - EXPLORE: High energy, innovation, branching
   - EXPAND: Low energy, preservation, crystallization

The final structure is a record of both the seed's information content
and the history of its available energy.
""")
