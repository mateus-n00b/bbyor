"""Server-side behaviours used to simulate faulty and strategic peers."""
import random
from typing import Protocol

from .config import Behaviour, Settings


class ServerBehaviour(Protocol):
    def should_serve(self, round_id: int, reputation: int) -> bool: ...


class Honest:
    def should_serve(self, round_id: int, reputation: int) -> bool:
        return True


class Intermittent:
    """Skips a round with a fixed probability (deterministic per seed and round)."""

    def __init__(self, fail_probability: float, seed: int):
        self.fail_probability = fail_probability
        self.seed = seed

    def should_serve(self, round_id: int, reputation: int) -> bool:
        return random.Random(f"{self.seed}:{round_id}").random() >= self.fail_probability


class OnOff:
    """Behaves until its reputation reaches the threshold, then stops serving."""

    def __init__(self, threshold: int):
        self.threshold = threshold

    def should_serve(self, round_id: int, reputation: int) -> bool:
        return reputation < self.threshold


def build_behaviour(settings: Settings) -> ServerBehaviour:
    match settings.behaviour:
        case Behaviour.HONEST:
            return Honest()
        case Behaviour.INTERMITTENT:
            return Intermittent(settings.fail_probability, settings.seed)
        case Behaviour.ON_OFF:
            return OnOff(settings.attack_threshold)
