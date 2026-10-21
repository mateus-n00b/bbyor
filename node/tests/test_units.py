import pytest
from pydantic import ValidationError

from bbyor.behaviour import Intermittent, OnOff
from bbyor.crypto.field import FIELD, to_field
from bbyor.crypto.schemes import PlainScheme
from bbyor.messages import Challenge, RequestChallenge, SignedResult, parse


def test_to_field_is_a_field_element():
    for data in (b"", b"x", b"\xff" * 1000):
        assert 0 <= to_field(data) < FIELD


def test_plain_scheme_roundtrip():
    s = PlainScheme()
    payload, expected = s.challenge(1234, nonce=FIELD - 1)
    assert s.respond(payload, FIELD - 1) == expected
    assert s.respond(payload, 5) != expected


def test_intermittent_is_deterministic_and_close_to_rate():
    b = Intermittent(fail_probability=0.3, seed=7)
    runs = [b.should_serve(r, 0) for r in range(2000)]
    assert runs == [Intermittent(0.3, 7).should_serve(r, 0) for r in range(2000)]
    assert 0.65 < sum(runs) / len(runs) < 0.75


def test_on_off_stops_at_threshold():
    b = OnOff(threshold=600)
    assert b.should_serve(1, 599)
    assert not b.should_serve(1, 600)


@pytest.mark.parametrize("msg", [
    Challenge(round=1, scheme="plain", payload="12"),
    RequestChallenge(round=2),
    SignedResult(round=3, result="9", signature="ab"),
])
def test_messages_roundtrip(msg):
    assert parse(msg.model_dump_json()) == msg


def test_unknown_message_is_rejected():
    with pytest.raises(ValidationError):
        parse('{"type": "hello"}')
