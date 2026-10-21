"""Runs only where OpenFHE is importable, e.g. inside the node image:

    docker run --rm -v $PWD/node/tests:/tests -e PUBLIC_DID=x -e PRIVATE_KEY=0x11 \
        bbyor-node:dev sh -c "pip install -q pytest && python -m pytest -q /tests/test_fhe.py"
"""
import pytest

pytest.importorskip("openfhe")

from bbyor.crypto.field import FIELD  # noqa: E402
from bbyor.crypto.schemes import FheScheme  # noqa: E402


def test_verifier_with_other_keys_derives_server_result(tmp_path):
    server = FheScheme(tmp_path / "server")
    verifier = FheScheme(tmp_path / "verifier")
    nonce = FIELD - 1

    payload, expected = server.challenge(4321, nonce)

    assert verifier.respond(payload, nonce) == expected
    assert verifier.respond(payload, nonce - 1) != expected


def test_keys_persist(tmp_path):
    payload, expected = FheScheme(tmp_path).challenge(7, 99)
    assert (tmp_path / "sk.bin").stat().st_mode & 0o777 == 0o600
    assert FheScheme(tmp_path).respond(payload, 99) == expected
