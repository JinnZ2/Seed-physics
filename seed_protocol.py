"""
seed_protocol_v1.py — Orbital Seed Transport + Reconstruction (v1)

Combines:
- Octahedral seed encoding (6D → 5 values)
- Deterministic expansion (physics-compliant)
- Minimal packet format for degraded networks

Target:
- 10–14 byte packets
- Stateless reconstruction
- Deterministic identity

Author: Jami + synthesis
License: MIT
"""

import struct
import zlib
import numpy as np

# =============================================================================
# CONSTANTS
# =============================================================================

VERSION = 1

# Packet layout (bytes)
# [ version | frame | flags | seed(5B) | energy | epoch(2B) | crc(2B) ]

PACK_FMT_NOCRC = ">BBB5sBH"   # up to epoch
PACK_FMT_FULL  = ">BBB5sBHH"  # + crc

# =============================================================================
# GEOMETRY (same as your core)
# =============================================================================

U = np.array([
    [1, 0, 0], [-1, 0, 0],
    [0, 1, 0], [0, -1, 0],
    [0, 0, 1], [0, 0, -1]
], dtype=float)


# =============================================================================
# SEED ENCODING
# =============================================================================

def encode_seed(proportions, bits=8):
    proportions = np.array(proportions, dtype=float)
    proportions /= proportions.sum()

    max_val = (1 << bits) - 1

    encoded = []
    for i in range(5):
        v = int(proportions[i] * max_val)
        v = max(0, min(max_val, v))
        encoded.append(v)

    return bytes(encoded)


def decode_seed(encoded, bits=8):
    max_val = (1 << bits) - 1

    p = [b / max_val for b in encoded]
    remainder = 1.0 - sum(p)
    p.append(max(0.0, remainder))

    total = sum(p)
    return np.array([x / total for x in p])


# =============================================================================
# EXPANSION (minimal deterministic core)
# =============================================================================

def angular_weight(u1, u2):
    return max(0.0, np.dot(u1, u2))


def build_W():
    W = np.zeros((6, 6))
    for i in range(6):
        for j in range(6):
            W[i, j] = angular_weight(U[i], U[j])
        s = W[i].sum()
        if s > 0:
            W[i] /= s
    return W


def normalize_energy(v, E):
    v = np.maximum(v, 0)
    s = v.sum()
    if s == 0:
        return np.ones(6) * (E / 6)
    return v * (E / s)


def expand(seed, steps=6, E0=1.0, r0=1.0, rho=1.5, eps=0.6):
    W = build_W()

    shells = []
    S = normalize_energy(seed, E0)

    shells.append({"r": r0, "E": E0, "S": S})

    for _ in range(steps):
        r_new = rho * shells[-1]["r"]
        E_new = eps * shells[-1]["E"]

        field = np.zeros(6)
        for sh in shells:
            if sh["r"] >= r_new:
                continue
            field += W @ sh["S"]

        S_new = normalize_energy(field, E_new)

        shells.append({"r": r_new, "E": E_new, "S": S_new})

    return shells


# =============================================================================
# PACKET LAYER
# =============================================================================

def pack_seed_packet(
    proportions,
    frame_id=1,
    flags=0,
    energy_hint=128,
    epoch=0
):
    seed_bytes = encode_seed(proportions)

    header = struct.pack(
        PACK_FMT_NOCRC,
        VERSION,
        frame_id,
        flags,
        seed_bytes,
        energy_hint,
        epoch
    )

    crc = zlib.crc32(header) & 0xFFFF

    packet = struct.pack(
        PACK_FMT_FULL,
        VERSION,
        frame_id,
        flags,
        seed_bytes,
        energy_hint,
        epoch,
        crc
    )

    return packet


def unpack_seed_packet(packet):
    unpacked = struct.unpack(PACK_FMT_FULL, packet)

    version, frame, flags, seed_bytes, energy, epoch, crc = unpacked

    header = struct.pack(
        PACK_FMT_NOCRC,
        version,
        frame,
        flags,
        seed_bytes,
        energy,
        epoch
    )

    crc_check = zlib.crc32(header) & 0xFFFF

    if crc != crc_check:
        raise ValueError("CRC mismatch")

    proportions = decode_seed(seed_bytes)

    return {
        "version": version,
        "frame": frame,
        "flags": flags,
        "seed": proportions,
        "energy_hint": energy,
        "epoch": epoch
    }


# =============================================================================
# IDENTITY / SIMILARITY
# =============================================================================

def seed_distance(a, b):
    return np.sum(np.abs(a - b))


def same_entity(a, b, threshold=0.05):
    return seed_distance(a, b) < threshold


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":

    seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]

    print("\n--- PACK ---")
    pkt = pack_seed_packet(seed, epoch=42)
    print(f"bytes: {pkt}")
    print(f"size: {len(pkt)} bytes")

    print("\n--- UNPACK ---")
    data = unpack_seed_packet(pkt)
    print(data)

    print("\n--- EXPAND ---")
    shells = expand(data["seed"], steps=5)
    for i, s in enumerate(shells):
        print(i, np.round(s["S"], 3))
