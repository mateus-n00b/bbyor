import random

def chance_30_percent(seed: int = None) -> bool:
    rng = random.Random(seed) if seed is not None else random
    return rng.random() < 0.3
