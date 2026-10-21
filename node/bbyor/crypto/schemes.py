"""Challenge schemes: how the server builds a challenge and how verifiers answer it.

Both sides must derive the same `result` (a field element) from the payload and
the round nonce; the server commits to Poseidon(result, nonce) on-chain.
"""
from pathlib import Path
from typing import Protocol

from .field import to_field


class ChallengeScheme(Protocol):
    name: str

    def challenge(self, secret: int, nonce: int) -> tuple[str, int]:
        """Returns (payload sent to verifiers, expected result)."""

    def respond(self, payload: str, nonce: int) -> int:
        """Returns the result a verifier derives from the payload."""


class PlainScheme:
    name = "plain"

    def challenge(self, secret: int, nonce: int) -> tuple[str, int]:
        payload = str(secret)
        return payload, self.respond(payload, nonce)

    def respond(self, payload: str, nonce: int) -> int:
        return to_field(str(int(payload) + nonce).encode())


class FheScheme:
    """BFV: the server encrypts `secret`, verifiers add the nonce homomorphically.

    EvalAdd with a plaintext is deterministic, so every verifier serializes the
    same ciphertext and hashes it to the same result.
    """

    name = "fhe"

    def __init__(self, key_dir: Path, metrics=None):
        import openfhe as fhe  # optional dependency, see pyproject extras

        self._fhe = fhe
        self._metrics = metrics
        params = fhe.CCParamsBFVRNS()
        params.SetPlaintextModulus(65537)
        params.SetMultiplicativeDepth(2)
        self._cc = fhe.GenCryptoContext(params)
        self._cc.Enable(fhe.PKESchemeFeature.PKE)
        self._cc.Enable(fhe.PKESchemeFeature.LEVELEDSHE)
        self._public_key = self._load_or_create_keys(key_dir)

    def _load_or_create_keys(self, key_dir: Path):
        fhe = self._fhe
        pk_path = key_dir / "pk.bin"
        if pk_path.exists():
            return fhe.DeserializePublicKeyString(pk_path.read_bytes(), fhe.BINARY)

        key_dir.mkdir(parents=True, exist_ok=True)
        keys = self._cc.KeyGen()
        fhe.SerializeToFile(str(pk_path), keys.publicKey, fhe.BINARY)
        sk_path = key_dir / "sk.bin"
        fhe.SerializeToFile(str(sk_path), keys.secretKey, fhe.BINARY)
        sk_path.chmod(0o600)
        return keys.publicKey

    def _add(self, ciphertext, nonce: int) -> bytes:
        # Plaintext slots live mod 65537; the full nonce is mixed in by the hash
        pt = self._cc.MakePackedPlaintext([nonce % 65537])
        summed = self._cc.EvalAdd(ciphertext, pt)
        return self._fhe.Serialize(summed, self._fhe.BINARY) + nonce.to_bytes(32, "big")

    def challenge(self, secret: int, nonce: int) -> tuple[str, int]:
        ct = self._cc.Encrypt(self._public_key, self._cc.MakePackedPlaintext([secret]))
        payload = self._fhe.Serialize(ct, self._fhe.BINARY).hex()
        # A fresh ciphertext serializes differently from a deserialized one, so
        # derive the expected result exactly the way verifiers will
        return payload, self.respond(payload, nonce)

    def respond(self, payload: str, nonce: int) -> int:
        ct = self._fhe.DeserializeCiphertextString(bytes.fromhex(payload), self._fhe.BINARY)
        return to_field(self._add(ct, nonce))


def build_scheme(name: str, key_dir: Path) -> ChallengeScheme:
    if name == "plain":
        return PlainScheme()
    if name == "fhe":
        return FheScheme(key_dir)
    raise ValueError(f"unknown scheme {name!r}")
