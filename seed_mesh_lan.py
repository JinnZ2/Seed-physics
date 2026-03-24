"""
seed_mesh_lan.py — Multi-Machine LAN UDP Mesh via Multicast

Extends seed_mesh_udp.py for real multi-machine deployment:
- IP multicast (224.1.1.1) for automatic peer discovery
- No hardcoded peer addresses
- Range filtering on virtual distance
- Packet loss and jitter simulation

Usage:
    # Run on each machine in the LAN:
    python seed_mesh_lan.py

Author: Jami + synthesis
License: MIT
"""

import socket
import struct
import threading
import numpy as np
import random
import time

# =============================================================================
# CONFIG
# =============================================================================

MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 50000

NUM_NODES_LOCAL = 1       # nodes per machine
COMM_RANGE = 200.0        # virtual distance range
SEED_DRIFT = 0.02
POS_DRIFT = 5.0
SIM_STEP = 1.0
PACKET_LOSS = 0.05
JITTER = 0.05


# =============================================================================
# PACKET UTILITIES
# =============================================================================

def pack_packet(node_id, seed, pos, energy=100, epoch=0):
    """Pack node_id + seed + position into binary packet."""
    return struct.pack('i6f3f2i', node_id, *(list(seed) + list(pos) + [energy, epoch]))


def unpack_packet(pkt):
    """Unpack binary packet."""
    data = struct.unpack('i6f3f2i', pkt)
    node_id = data[0]
    seed = np.array(data[1:7])
    pos = np.array(data[7:10])
    energy, epoch = data[10:12]
    return {"id": node_id, "seed": seed, "position": pos, "energy": energy, "epoch": epoch}


def combine_seeds(seeds):
    """Combine multiple seeds by averaging."""
    return np.mean(seeds, axis=0)


# =============================================================================
# NODE DEFINITION
# =============================================================================

class Node:
    def __init__(self, node_id):
        self.id = node_id
        self.pos = np.random.rand(3) * 1000.0
        s = np.random.rand(6)
        self.seed = s / s.sum()
        self.energy = random.randint(80, 200)
        self.epoch = 0
        self.inbox = []
        self.lock = threading.Lock()

    def broadcast(self, sock):
        """Broadcast to multicast group with simulated loss/jitter."""
        pkt = pack_packet(self.id, self.seed, self.pos, self.energy, self.epoch)
        if random.random() < PACKET_LOSS:
            return
        delay = random.uniform(0, JITTER)
        threading.Timer(
            delay,
            lambda: sock.sendto(pkt, (MULTICAST_GROUP, MULTICAST_PORT))
        ).start()

    def update(self):
        """Update seed and position from received neighbors."""
        with self.lock:
            if not self.inbox:
                return
            neighbor_seeds = [msg["seed"] for msg in self.inbox if msg["id"] != self.id]
            neighbor_positions = [msg["position"] for msg in self.inbox if msg["id"] != self.id]
            if neighbor_seeds:
                self.seed = (1 - SEED_DRIFT) * self.seed + SEED_DRIFT * combine_seeds([self.seed] + neighbor_seeds)
                self.seed /= self.seed.sum()
            if neighbor_positions:
                avg_pos = np.mean(neighbor_positions, axis=0)
                self.pos += POS_DRIFT * (avg_pos - self.pos) / (np.linalg.norm(avg_pos - self.pos) + 1e-6)
                self.pos += np.random.randn(3) * 0.5
            self.inbox = []
            self.epoch += 1


# =============================================================================
# MULTICAST SOCKET
# =============================================================================

def create_multicast_socket():
    """Create a UDP socket joined to the multicast group."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))
    mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setblocking(False)
    return sock


# =============================================================================
# RECEIVE LOOP
# =============================================================================

def receive_loop(sock, nodes):
    """Background loop: receive multicast packets and route to nodes."""
    while True:
        try:
            pkt, addr = sock.recvfrom(1024)
            data = unpack_packet(pkt)
            # Range filtering (virtual distance)
            for n in nodes:
                dist = np.linalg.norm(n.pos - data["position"])
                if dist <= COMM_RANGE:
                    with n.lock:
                        n.inbox.append(data)
        except BlockingIOError:
            time.sleep(0.01)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":

    nodes = [Node(i) for i in range(NUM_NODES_LOCAL)]
    sock = create_multicast_socket()

    t = threading.Thread(target=receive_loop, args=(sock, nodes), daemon=True)
    t.start()

    print(f"\n=== LAN MESH (multicast {MULTICAST_GROUP}:{MULTICAST_PORT}) ===\n")

    try:
        while True:
            for n in nodes:
                n.broadcast(sock)
            time.sleep(SIM_STEP)
            for n in nodes:
                n.update()
            seed_var = np.mean([np.var(n.seed) for n in nodes])
            positions = np.array([n.pos for n in nodes])
            centroid = np.mean(positions, axis=0)
            spread = np.mean(np.linalg.norm(positions - centroid, axis=1))
            print(f"epoch {nodes[0].epoch} | seed_var={seed_var:.4f} | spread={spread:.2f}")
    except KeyboardInterrupt:
        print("\nLAN mesh terminated.")
