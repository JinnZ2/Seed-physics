"""
seed_mesh_udp.py — Range-Limited UDP Mesh with Jitter

Real UDP mesh on localhost with:
- Range-limited communication (virtual distance)
- Packet loss simulation
- Jitter (random delay)
- Seed convergence via field coupling
- Position drift toward similar seeds

Usage:
    python seed_mesh_udp.py

Author: Jami + synthesis
License: MIT
"""

import socket
import threading
import numpy as np
import struct
import random
import time

# =============================================================================
# CONFIG
# =============================================================================

NUM_NODES = 5
BASE_PORT = 50000
COMM_RANGE = 200.0     # max distance for messages
SEED_DRIFT = 0.02
POS_DRIFT = 5.0
SIM_STEP = 1.0         # seconds per simulation step

PACKET_LOSS = 0.1      # 10% packet drop
JITTER = 0.05          # seconds of random delay


# =============================================================================
# PACKET UTILITIES
# =============================================================================

def pack_packet(seed, pos, energy=100, epoch=0):
    """Pack seed + position into binary packet."""
    return struct.pack('6f3f2i', *(list(seed) + list(pos) + [energy, epoch]))


def unpack_packet(pkt):
    """Unpack binary packet to seed + position."""
    data = struct.unpack('6f3f2i', pkt)
    seed = np.array(data[0:6])
    pos = np.array(data[6:9])
    energy, epoch = data[9:11]
    return {"seed": seed, "position": pos, "energy": energy, "epoch": epoch}


# =============================================================================
# SEED UTILITIES
# =============================================================================

def combine_seeds(seeds):
    """Combine multiple seeds by averaging."""
    return np.mean(seeds, axis=0)


# =============================================================================
# NODE DEFINITION
# =============================================================================

class Node:
    def __init__(self, node_id, port):
        self.id = node_id
        self.port = port
        self.pos = np.random.rand(3) * 1000.0
        s = np.random.rand(6)
        self.seed = s / s.sum()
        self.energy = random.randint(80, 200)
        self.epoch = 0
        self.inbox = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', self.port))
        self.sock.setblocking(False)
        self.lock = threading.Lock()

    def broadcast(self, nodes):
        """Broadcast with range filtering, packet loss, and jitter."""
        pkt = pack_packet(self.seed, self.pos, self.energy, self.epoch)
        for n in nodes:
            if n.port == self.port:
                continue
            dist = np.linalg.norm(self.pos - n.pos)
            if dist > COMM_RANGE:
                continue
            if random.random() < PACKET_LOSS:
                continue
            # Simulate jitter
            target_port = n.port
            delay = random.uniform(0, JITTER)
            threading.Timer(
                delay,
                lambda p=target_port: self.sock.sendto(pkt, ('localhost', p))
            ).start()

    def receive_loop(self):
        """Background receive loop."""
        while True:
            try:
                pkt, addr = self.sock.recvfrom(1024)
                data = unpack_packet(pkt)
                with self.lock:
                    self.inbox.append(data)
            except BlockingIOError:
                time.sleep(0.01)

    def update(self):
        """Update seed and position from received neighbors."""
        with self.lock:
            if not self.inbox:
                return
            neighbor_seeds = [msg["seed"] for msg in self.inbox]
            neighbor_positions = [msg["position"] for msg in self.inbox]

            # Seed update
            self.seed = (1 - SEED_DRIFT) * self.seed + SEED_DRIFT * combine_seeds([self.seed] + neighbor_seeds)
            self.seed /= self.seed.sum()

            # Position update
            avg_pos = np.mean(neighbor_positions, axis=0)
            self.pos += POS_DRIFT * (avg_pos - self.pos) / (np.linalg.norm(avg_pos - self.pos) + 1e-6)
            self.pos += np.random.randn(3) * 0.5

            self.inbox = []
            self.epoch += 1


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    nodes = []
    ports = [BASE_PORT + i for i in range(NUM_NODES)]

    for i in range(NUM_NODES):
        n = Node(i, ports[i])
        t = threading.Thread(target=n.receive_loop, daemon=True)
        t.start()
        nodes.append(n)

    print(f"\n=== UDP MESH ({NUM_NODES} nodes, range={COMM_RANGE}, loss={PACKET_LOSS:.0%}) ===\n")

    try:
        while True:
            for n in nodes:
                n.broadcast(nodes)
            time.sleep(SIM_STEP)
            for n in nodes:
                n.update()
            # Show metrics
            seed_var = np.mean([np.var(n.seed) for n in nodes])
            positions = np.array([n.pos for n in nodes])
            centroid = np.mean(positions, axis=0)
            spread = np.mean(np.linalg.norm(positions - centroid, axis=1))
            print(f"epoch {nodes[0].epoch} | seed_var={seed_var:.4f} | spread={spread:.2f}")
    except KeyboardInterrupt:
        print("\nUDP mesh terminated.")
