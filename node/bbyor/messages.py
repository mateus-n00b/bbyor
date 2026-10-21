"""DIDComm basic-message payloads exchanged between nodes."""
from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, TypeAdapter


class Challenge(BaseModel):
    type: Literal["challenge"] = "challenge"
    round: int
    scheme: str
    payload: str


class RequestChallenge(BaseModel):
    type: Literal["request_challenge"] = "request_challenge"
    round: int


class SignedResult(BaseModel):
    """Baseline attestation: verifier signs the result instead of proving it on-chain."""
    type: Literal["signed_result"] = "signed_result"
    round: int
    result: str
    signature: str


Message = Annotated[Union[Challenge, RequestChallenge, SignedResult], Field(discriminator="type")]
_adapter = TypeAdapter(Message)


def parse(content: str) -> Message:
    return _adapter.validate_json(content)
