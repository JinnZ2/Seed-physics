"""
ConstraintAgent: Seed-native agent with bloom/explore/compress lifecycle.

An agent rooted in seed geometry that expands outward (bloom), traverses
its discovered constraint space (explore), and collapses back to a compact
seed representation (compress). The geometric map survives compression,
enabling deterministic re-expansion.

Uses exact-rational arithmetic (fractions) for energy accounting to avoid
floating-point drift across expansion cycles.

Standalone — no external agent framework required.

Author: Jami (Kavik Ulu) - MIT License
"""

import ast
from dataclasses import dataclass, field
from enum import Enum
from fractions import Fraction
from typing import Dict, List, Optional


# =============================================================================
# STATE & BUDGET
# =============================================================================

class AgentState(Enum):
    COMPRESSED = "compressed"
    EXPANDING = "expanding"
    EXPLORING = "exploring"
    CONTRACTING = "contracting"


@dataclass
class ResourceBudget:
    compute: int = 0
    bandwidth: float = 0.0
    energy: Fraction = Fraction(1, 1)
    time_remaining: Fraction = Fraction(1, 1)

    def is_depleted(self) -> bool:
        return self.energy <= 0 or self.compute <= 0


# =============================================================================
# GEOMETRIC MAP
# =============================================================================

@dataclass
class GeometricMap:
    """Discovered constraint geometry: resonances, relationships, energy flows."""
    resonances: Dict[str, Fraction] = field(default_factory=dict)
    relationships: Dict[str, list] = field(default_factory=dict)
    energy_flows: Dict[tuple, Fraction] = field(default_factory=dict)

    def record_resonance(self, entity_id: str, score: float) -> None:
        self.resonances[entity_id] = Fraction(score).limit_denominator(10000)

    def record_relationship(self, from_id: str, to_id: str) -> None:
        self.relationships.setdefault(from_id, [])
        if to_id not in self.relationships[from_id]:
            self.relationships[from_id].append(to_id)

    def record_energy_flow(self, from_id: str, to_id: str, amount: Fraction) -> None:
        key = (from_id, to_id)
        self.energy_flows[key] = self.energy_flows.get(key, Fraction(0, 1)) + amount


# =============================================================================
# CONSTRAINT AGENT
# =============================================================================

class ConstraintAgent:
    """
    Seed-native agent with bloom/explore/compress lifecycle.

    Lifecycle:
        compressed -> bloom() -> expanding -> explore() -> exploring -> compress() -> compressed

    The geometric map survives compression. Re-expansion from a prior map
    is deterministic — same seed + same map = same structure.
    """

    def __init__(self, seed_id: str, home_families: List[str] = None,
                 bloom_threshold: Fraction = Fraction(1, 10)):
        self.seed_id = seed_id
        self.home_families = home_families or []
        self.bloom_threshold = bloom_threshold

        self.state = AgentState.COMPRESSED
        self.compression_ratio = Fraction(1, 1)
        self.current_position = seed_id

        self.budget = ResourceBudget()
        self.map = GeometricMap()
        self.expansion_history: List[dict] = []
        self.sensor_state: Dict[str, Fraction] = {}

    # -----------------------------------------------------------------
    # Resource management
    # -----------------------------------------------------------------

    def set_resource_budget(self, compute: int = 0, bandwidth: float = 0.0,
                            energy: float = 1.0, time_remaining: float = 1.0) -> None:
        """Set available resources for expansion."""
        self.budget = ResourceBudget(
            compute=compute,
            bandwidth=bandwidth,
            energy=Fraction(energy).limit_denominator(10000),
            time_remaining=Fraction(time_remaining).limit_denominator(10000)
        )

    def should_expand(self) -> bool:
        """Check if resources exceed bloom threshold."""
        if self.budget.is_depleted():
            return False
        energy_ratio = self.budget.energy / max(self.budget.energy, Fraction(1, 1))
        return energy_ratio >= self.bloom_threshold

    # -----------------------------------------------------------------
    # Bloom: expand outward from seed
    # -----------------------------------------------------------------

    def bloom(self, depth: int = 1, seed_map: Optional[GeometricMap] = None) -> List[str]:
        """
        Expand outward from seed, discovering new entities up to depth.
        If seed_map provided, re-expand deterministically along previous discoveries.

        Returns list of newly discovered entity IDs.
        """
        if self.state == AgentState.COMPRESSED:
            self.state = AgentState.EXPANDING

        discovered = []
        frontier = [self.seed_id]

        # If we have a prior map, expand along known relationships first
        if seed_map and seed_map.relationships:
            for entity_id in frontier:
                if entity_id in seed_map.relationships:
                    for reachable in seed_map.relationships[entity_id]:
                        if reachable not in self.map.resonances:
                            discovered.append(reachable)
                            if reachable in seed_map.resonances:
                                self.map.resonances[reachable] = seed_map.resonances[reachable]

        # Explore new entities
        current_depth = 0
        while current_depth < depth and not self.budget.is_depleted():
            new_frontier = []
            for entity_id in frontier:
                neighbors = self._get_neighbors(entity_id, depth - current_depth)
                for neighbor_id, resonance_score in neighbors:
                    if neighbor_id not in self.map.resonances:
                        self.map.record_resonance(neighbor_id, resonance_score)
                        self.map.record_relationship(entity_id, neighbor_id)
                        discovered.append(neighbor_id)
                        new_frontier.append(neighbor_id)
                        self.budget.compute = max(0, self.budget.compute - 10)
                        self.budget.energy -= Fraction(1, 100)

            frontier = new_frontier
            current_depth += 1

        self.expansion_history.append({
            "depth": depth,
            "discovered_entities": discovered,
            "energy_spent": Fraction(1, 100) * len(discovered)
        })

        self.state = AgentState.EXPLORING
        self.compression_ratio = Fraction(0, 1)
        return discovered

    # -----------------------------------------------------------------
    # Explore: traverse expanded constraint space
    # -----------------------------------------------------------------

    def explore(self) -> Dict[str, any]:
        """
        Traverse the expanded constraint space, recording energy flows
        and sensor activations. Returns discovery summary.
        """
        if self.state not in [AgentState.EXPANDING, AgentState.EXPLORING]:
            return {}

        self.state = AgentState.EXPLORING
        summary = {
            "entities_visited": 0,
            "relationships_mapped": 0,
            "energy_flows_recorded": 0,
            "sensor_activations": {}
        }

        for from_id in self.map.relationships:
            for to_id in self.map.relationships[from_id]:
                if from_id in self.map.resonances and to_id in self.map.resonances:
                    flow = self.map.resonances[from_id] * self.map.resonances[to_id]
                    self.map.record_energy_flow(from_id, to_id, flow)
                    summary["energy_flows_recorded"] += 1
                    summary["entities_visited"] += 1

        summary["relationships_mapped"] = len(self.map.relationships)
        self._update_sensors()
        summary["sensor_activations"] = dict(self.sensor_state)

        return summary

    # -----------------------------------------------------------------
    # Compress: collapse back to seed
    # -----------------------------------------------------------------

    def compress(self) -> Fraction:
        """
        Collapse back to seed geometry, preserving the map.
        Returns compression ratio (0 = fully expanded, 1 = fully compressed).
        """
        if self.state == AgentState.COMPRESSED:
            return self.compression_ratio

        self.state = AgentState.CONTRACTING
        self.compression_ratio = Fraction(1, 1)
        self.current_position = self.seed_id
        self.state = AgentState.COMPRESSED
        return self.compression_ratio

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    def detect_corruption(self, imposed_constraint: str) -> bool:
        """
        Check if an imposed external constraint violates the agent's own map.
        Returns True if corruption detected.
        """
        # Hook: compare imposed_constraint against discovered resonances/relationships
        return False

    def self_validate(self) -> Dict[str, any]:
        """
        Internal consistency check: verify map integrity, detect anomalies.
        Returns validation report.
        """
        report = {
            "is_valid": True,
            "inconsistencies": [],
            "energy_balance": Fraction(0, 1),
            "geometry_coherence": Fraction(1, 1)
        }

        # Check energy conservation in recorded flows
        inflows: Dict[str, Fraction] = {}
        outflows: Dict[str, Fraction] = {}
        for (from_id, to_id), amount in self.map.energy_flows.items():
            outflows[from_id] = outflows.get(from_id, Fraction(0, 1)) + amount
            inflows[to_id] = inflows.get(to_id, Fraction(0, 1)) + amount

        for entity_id in set(list(inflows.keys()) + list(outflows.keys())):
            imbalance = inflows.get(entity_id, Fraction(0, 1)) - outflows.get(entity_id, Fraction(0, 1))
            if imbalance != 0:
                report["inconsistencies"].append(
                    f"{entity_id}: energy imbalance = {imbalance}"
                )
                report["is_valid"] = False

        # Check resonance coherence (scores should be 0 to 1)
        for entity_id, score in self.map.resonances.items():
            if score < 0 or score > 1:
                report["inconsistencies"].append(
                    f"{entity_id}: resonance out of range ({score})"
                )
                report["is_valid"] = False

        return report

    # -----------------------------------------------------------------
    # Extension hooks (override or replace for real integrations)
    # -----------------------------------------------------------------

    def _get_neighbors(self, entity_id: str, remaining_depth: int) -> List[tuple]:
        """
        Fetch neighbors from external system (Rosetta, Mandala, etc.).
        Override for real entity lookups.

        Returns list of (neighbor_id, resonance_score) tuples.
        """
        return []

    def _update_sensors(self) -> None:
        """
        Update sensor state based on discovered geometry.
        Override to integrate with Emotions-as-Sensors or similar.
        """
        self.sensor_state = {
            "expansion_drive": Fraction(0, 1),
            "stability_need": Fraction(0, 1),
            "boundary_awareness": Fraction(0, 1)
        }

    # -----------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------

    def serialize(self) -> Dict[str, any]:
        """Serialize agent state to JSON-compatible dict."""
        return {
            "seed_id": self.seed_id,
            "home_families": self.home_families,
            "state": self.state.value,
            "compression_ratio": (self.compression_ratio.numerator, self.compression_ratio.denominator),
            "budget": {
                "compute": self.budget.compute,
                "bandwidth": self.budget.bandwidth,
                "energy": (self.budget.energy.numerator, self.budget.energy.denominator),
                "time_remaining": (self.budget.time_remaining.numerator, self.budget.time_remaining.denominator)
            },
            "map": {
                "resonances": {
                    k: (v.numerator, v.denominator) for k, v in self.map.resonances.items()
                },
                "relationships": self.map.relationships,
                "energy_flows": {
                    str(k): (v.numerator, v.denominator) for k, v in self.map.energy_flows.items()
                }
            },
            "expansion_history": [
                {
                    "depth": h["depth"],
                    "discovered_entities": h["discovered_entities"],
                    "energy_spent": (h["energy_spent"].numerator, h["energy_spent"].denominator)
                }
                for h in self.expansion_history
            ],
            "sensor_state": {
                k: (v.numerator, v.denominator) for k, v in self.sensor_state.items()
            }
        }

    @classmethod
    def deserialize(cls, data: Dict[str, any]) -> "ConstraintAgent":
        """Reconstruct agent from serialized state."""
        agent = cls(
            seed_id=data["seed_id"],
            home_families=data["home_families"]
        )
        agent.state = AgentState(data["state"])
        agent.compression_ratio = Fraction(
            data["compression_ratio"][0],
            data["compression_ratio"][1]
        )
        agent.budget = ResourceBudget(
            compute=data["budget"]["compute"],
            bandwidth=data["budget"]["bandwidth"],
            energy=Fraction(data["budget"]["energy"][0], data["budget"]["energy"][1]),
            time_remaining=Fraction(data["budget"]["time_remaining"][0], data["budget"]["time_remaining"][1])
        )
        agent.map.resonances = {
            k: Fraction(v[0], v[1]) for k, v in data["map"]["resonances"].items()
        }
        agent.map.relationships = data["map"]["relationships"]
        agent.map.energy_flows = {
            ast.literal_eval(k): Fraction(v[0], v[1])
            for k, v in data["map"]["energy_flows"].items()
        }
        agent.expansion_history = [
            {
                "depth": h["depth"],
                "discovered_entities": h["discovered_entities"],
                "energy_spent": Fraction(h["energy_spent"][0], h["energy_spent"][1])
            }
            for h in data["expansion_history"]
        ]
        agent.sensor_state = {
            k: Fraction(v[0], v[1]) for k, v in data["sensor_state"].items()
        }
        return agent


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CONSTRAINT AGENT - Bloom/Explore/Compress Lifecycle")
    print("=" * 60)

    agent = ConstraintAgent(
        seed_id="SHAPE.TETRA",
        home_families=["stability", "foundation"]
    )

    agent.set_resource_budget(compute=1000, bandwidth=10.0, energy=1.0, time_remaining=1.0)

    print(f"\nAgent: {agent.seed_id}")
    print(f"State: {agent.state.value}")
    print(f"Should expand: {agent.should_expand()}")

    # Bloom
    if agent.should_expand():
        discovered = agent.bloom(depth=2)
        print(f"\nBloom discovered: {discovered}")

    # Explore
    exploration = agent.explore()
    print(f"Exploration: {exploration}")

    # Self-validate
    validation = agent.self_validate()
    print(f"Validation: {validation}")

    # Compress
    compression = agent.compress()
    print(f"\nCompressed. Ratio: {compression}")
    print(f"State: {agent.state.value}")

    # Re-expand from prior map
    agent.set_resource_budget(compute=500, energy=0.5)
    if agent.should_expand():
        rediscovered = agent.bloom(depth=1, seed_map=agent.map)
        print(f"Re-expansion: {rediscovered}")

    # Corruption check
    print(f"Corruption detected: {agent.detect_corruption('test')}")

    # Round-trip serialization
    serialized = agent.serialize()
    restored = ConstraintAgent.deserialize(serialized)
    print(f"\nSerialized & restored: {restored.seed_id}, state={restored.state.value}")
    print(f"Map preserved: {len(restored.map.resonances)} resonances")

    print("\n" + "=" * 60)
    print("Lifecycle complete.")
