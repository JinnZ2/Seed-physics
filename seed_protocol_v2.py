"""
seed_protocol_v2.py — Seed Protocol with Spatial Coupling

Extends v1 with:
- Position encoding (anchor cell + local offset)
- Neighbor hint (directional bias for routing)
- 21-byte packets for spatially-aware mesh networks

Packet layout (21 bytes):
    Offset  Size  Field
    ------  ----  ------------------------------
    0       1     Version
    1       1     Frame ID
    2       1     Flags
    3       5     Seed (5 x uint8)
    8       1     Energy Hint (uint8)
    9       2     Epoch (uint16)
    11      2     Anchor Cell (uint16)
    13      3     Offset Vector (int8 x 3)
    16      3     Neighbor Hint (dir_idx + projection)
    19      2     CRC16

Author: Jami + synthesis
License: MIT
"""

import struct
import zlib
import numpy as np

# =============================================================================
# CONSTANTS
# =============================================================================

VERSION = 2

# > = big endian
# B B B     = version, frame, flags
# 5s        = seed (5 bytes)
# B         = energy
# H         = epoch
# H         = anchor
# 3b        = offset (x,y,z)
# B H       = neighbor hint (dir_idx, projection)
# H         = CRC16

PACK_FMT_NOCRC = ">BBB5sBHH3bBH"
PACK_FMT_FULL  = ">BBB5sBHH3bBHH"

# =============================================================================
# GEOMETRY
# =============================================================================

U = np.array([
    [1, 0, 0], [-1, 0, 0],
    [0, 1, 0], [0, -1, 0],
    [0, 0, 1], [0, 0, -1]
], dtype=float)

# =============================================================================
# SEED ENCODING / DECODING
# =============================================================================

def encode_seed(proportions):
    """Encode 6 proportional values to 5 bytes."""
    p = np.array(proportions, dtype=float)
    p /= p.sum()

    encoded = []
    for i in range(5):
        val = int(p[i] * 255)
        val = max(0, min(255, val))
        encoded.append(val)

    return bytes(encoded)


def decode_seed(encoded):
    """Decode 5 bytes to 6 proportional values."""
    p = [b / 255.0 for b in encoded]
    remainder = 1.0 - sum(p)
    p.append(max(0.0, remainder))

    p = np.array(p)
    return p / p.sum()


# =============================================================================
# POSITION ENCODING
# =============================================================================

GRID_SCALE = 100.0  # meters per cell

def position_to_anchor_offset(pos):
    """Encode 3D position as anchor cell ID + local offset."""
    pos = np.array(pos)

    anchor = np.floor(pos / GRID_SCALE).astype(int)
    anchor_id = ((anchor[0] & 0x1F) << 10) | ((anchor[1] & 0x1F) << 5) | (anchor[2] & 0x1F)

    local = pos - (anchor * GRID_SCALE)
    offset = np.clip((local / GRID_SCALE * 127), -128, 127).astype(int)

    return anchor_id, offset


def anchor_offset_to_position(anchor_id, offset):
    """Decode anchor cell ID + offset back to 3D position."""
    x = (anchor_id >> 10) & 0x1F
    y = (anchor_id >> 5) & 0x1F
    z = anchor_id & 0x1F

    anchor = np.array([x, y, z], dtype=float)
    base = anchor * GRID_SCALE

    offset = np.array(offset) / 127.0 * GRID_SCALE

    return base + offset


# =============================================================================
# NEIGHBOR HINT
# =============================================================================

def encode_neighbor_hint(seed):
    """Encode dominant direction as routing hint."""
    idx = int(np.argmax(seed))
    proj = int(seed[idx] * 65535)
    return idx, proj


def decode_neighbor_hint(idx, proj):
    """Decode routing hint to direction + strength."""
    direction = U[idx]
    strength = proj / 65535.0
    return direction, strength


# =============================================================================
# CRC
# =============================================================================

def compute_crc(data):
    """CRC16 from lower 16 bits of CRC32."""
    return zlib.crc32(data) & 0xFFFF


# =============================================================================
# PACK / UNPACK
# =============================================================================

def pack_packet(seed, pos, energy=128, epoch=0, frame=1, flags=0):
    """Pack seed + position into a 21-byte transport packet."""
    seed_bytes = encode_seed(seed)

    anchor, offset = position_to_anchor_offset(pos)
    dx, dy, dz = offset

    dir_idx, proj = encode_neighbor_hint(seed)

    header = struct.pack(
        PACK_FMT_NOCRC,
        VERSION,
        frame,
        flags,
        seed_bytes,
        energy,
        epoch,
        anchor,
        dx, dy, dz,
        dir_idx,
        proj
    )

    crc = compute_crc(header)

    packet = struct.pack(
        PACK_FMT_FULL,
        VERSION,
        frame,
        flags,
        seed_bytes,
        energy,
        epoch,
        anchor,
        dx, dy, dz,
        dir_idx,
        proj,
        crc
    )

    return packet


def unpack_packet(packet):
    """Unpack and verify a v2 transport packet."""
    unpacked = struct.unpack(PACK_FMT_FULL, packet)

    (version, frame, flags, seed_bytes, energy, epoch,
     anchor, dx, dy, dz, dir_idx, proj, crc) = unpacked

    header = struct.pack(
        PACK_FMT_NOCRC,
        version, frame, flags, seed_bytes,
        energy, epoch, anchor,
        dx, dy, dz,
        dir_idx, proj
    )

    if compute_crc(header) != crc:
        raise ValueError("CRC mismatch")

    seed = decode_seed(seed_bytes)
    pos = anchor_offset_to_position(anchor, (dx, dy, dz))
    direction, strength = decode_neighbor_hint(dir_idx, proj)

    return {
        "version": version,
        "frame": frame,
        "flags": flags,
        "seed": seed,
        "energy": energy,
        "epoch": epoch,
        "position": pos,
        "neighbor_direction": direction,
        "neighbor_strength": strength
    }


# =============================================================================
# UTILITIES
# =============================================================================

def seed_distance(a, b):
    """L1 distance between two seed vectors."""
    return np.sum(np.abs(a - b))


def combine_seeds(seeds):
    """Combine multiple seeds by averaging."""
    S = np.sum(seeds, axis=0)
    return S / S.sum()


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":

    seed = [0.5, 0.2, 0.15, 0.08, 0.05, 0.02]
    pos = [123.4, 456.7, 78.9]

    print("\n--- PACK ---")
    pkt = pack_packet(seed, pos, epoch=42)
    print("packet bytes:", pkt)
    print("size:", len(pkt), "bytes")

    print("\n--- UNPACK ---")
    data = unpack_packet(pkt)

    print("decoded seed:", np.round(data["seed"], 4))
    print("decoded position:", np.round(data["position"], 2))
    print("neighbor dir:", data["neighbor_direction"])
    print("neighbor strength:", round(data["neighbor_strength"], 3))

    print("\n--- DISTANCE CHECK ---")
    print("seed error:", np.max(np.abs(data["seed"] - np.array(seed) / sum(seed))))
