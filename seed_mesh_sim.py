"""
seed_mesh_sim.py — In-Process Multi-Node Mesh Simulation

Simulates a network of seed nodes that:
- Broadcast v2 packets within communication range
- Converge seeds via field coupling
- Drift positions toward similar seeds
- Self-organize into spatially coherent clusters

Includes gradient-based routing test.

Author: Jami + synthesis
License: MIT
"""

import numpy as np
import random

from seed_protocol_v2 import (
    pack_packet,
    unpack_packet,
    seed_distance,
    combine_seeds
)

# =============================================================================
# CONFIG
# =============================================================================

NUM_NODES = 40
SPACE_SIZE = 1000.0
COMM_RANGE = 200.0
STEPS = 50

SEED_DRIFT = 0.02
POS_DRIFT = 5.0


# =============================================================================
# NODE DEFINITION
# =============================================================================

class Node:
    def __init__(self, node_id):
        self.id = node_id

        # Random position
        self.pos = np.random.rand(3) * SPACE_SIZE

        # Random seed (normalized)
        s = np.random.rand(6)
        self.seed = s / s.sum()

        self.energy = random.randint(80, 200)
        self.epoch = 0

        self.inbox = []

    def broadcast(self):
        """Create a packet for broadcasting."""
        pkt = pack_packet(
            self.seed,
            self.pos,
            energy=self.energy,
            epoch=self.epoch
        )
        return pkt

    def receive(self, pkt):
        """Receive and decode a packet."""
        try:
            data = unpack_packet(pkt)
            self.inbox.append(data)
        except Exception:
            pass  # drop corrupted

    def update(self):
        """Update seed and position from received neighbors."""
        if not self.inbox:
            return

        neighbor_seeds = []
        neighbor_positions = []

        for msg in self.inbox:
            neighbor_seeds.append(msg["seed"])
            neighbor_positions.append(msg["position"])

        # Seed update (field coupling)
        combined = combine_seeds([self.seed] + neighbor_seeds)
        self.seed = (1 - SEED_DRIFT) * self.seed + SEED_DRIFT * combined
        self.seed /= self.seed.sum()

        # Position update (attraction)
        avg_pos = np.mean(neighbor_positions, axis=0)
        self.pos += POS_DRIFT * (avg_pos - self.pos) / (np.linalg.norm(avg_pos - self.pos) + 1e-6)

        # Small noise to prevent collapse
        self.pos += np.random.randn(3) * 0.5

        # Clear inbox
        self.inbox = []
        self.epoch += 1


# =============================================================================
# SIMULATION
# =============================================================================

def distance(a, b):
    return np.linalg.norm(a - b)


def step_sim(nodes):
    """Run one simulation step: broadcast, receive, update."""
    # Broadcast phase
    packets = []
    for node in nodes:
        pkt = node.broadcast()
        packets.append((node, pkt))

    # Receive phase (range-limited)
    for sender, pkt in packets:
        for receiver in nodes:
            if sender.id == receiver.id:
                continue
            if distance(sender.pos, receiver.pos) < COMM_RANGE:
                receiver.receive(pkt)

    # Update phase
    for node in nodes:
        node.update()


def compute_metrics(nodes):
    """Compute seed variance and spatial spread."""
    seeds = np.array([n.seed for n in nodes])
    positions = np.array([n.pos for n in nodes])

    seed_var = np.mean(np.var(seeds, axis=0))

    centroid = np.mean(positions, axis=0)
    spatial_spread = np.mean(np.linalg.norm(positions - centroid, axis=1))

    return seed_var, spatial_spread


# =============================================================================
# ROUTING
# =============================================================================

def route(nodes, source_id, target_id, max_hops=10):
    """Route from source to target using seed + position gradient."""
    current = nodes[source_id]
    target = nodes[target_id]

    path = [current.id]

    for _ in range(max_hops):
        # Find neighbors in range
        neighbors = [
            n for n in nodes
            if n.id != current.id and distance(n.pos, current.pos) < COMM_RANGE
        ]

        if not neighbors:
            break

        # Choose best next hop
        next_node = min(
            neighbors,
            key=lambda n:
                0.7 * seed_distance(n.seed, target.seed) +
                0.3 * distance(n.pos, target.pos)
        )

        current = next_node
        path.append(current.id)

        if current.id == target.id:
            break

    return path


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    nodes = [Node(i) for i in range(NUM_NODES)]

    print("\n=== SIMULATION START ===\n")

    for step in range(STEPS):
        step_sim(nodes)

        if step % 5 == 0:
            seed_var, spread = compute_metrics(nodes)
            print(f"step {step:02d} | seed_var={seed_var:.4f} | spread={spread:.2f}")

    print("\n=== FINAL STATE ===\n")

    # Show a few nodes
    for i in range(5):
        n = nodes[i]
        print(f"Node {n.id}")
        print("  pos:", np.round(n.pos, 1))
        print("  seed:", np.round(n.seed, 3))
        print()

    # Routing test
    print("\n=== ROUTING TEST ===\n")

    src = 0
    dst = random.randint(1, NUM_NODES - 1)

    path = route(nodes, src, dst)

    print(f"Route {src} -> {dst}:")
    print(" -> ".join(map(str, path)))
