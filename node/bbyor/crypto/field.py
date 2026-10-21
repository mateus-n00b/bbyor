import hashlib

# BN254 scalar field (same as the circuit and Reputation.FIELD)
FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617


def to_field(data: bytes) -> int:
    """Hashes arbitrary bytes into a field element (31 bytes of SHA-256 < FIELD)."""
    return int.from_bytes(hashlib.sha256(data).digest()[:31], "big")
