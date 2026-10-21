from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Scheme(str, Enum):
    FHE = "fhe"
    PLAIN = "plain"


class Attestation(str, Enum):
    ZK = "zk"
    SIGNATURE = "signature"


class Behaviour(str, Enum):
    HONEST = "honest"
    INTERMITTENT = "intermittent"  # skips serving with probability FAIL_PROBABILITY
    ON_OFF = "on_off"              # serves only while reputation < ATTACK_THRESHOLD


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Agent ---
    acapy_url: str = Field("http://localhost:8250", description="ACA-Py admin API")
    public_did: str = Field(..., description="This node's public DID (as registered on-chain)")

    # --- Chain ---
    provider_url: str = "http://localhost:8545"
    private_key: str
    deployment_file: Path = Path("sim/out/deployment.json")
    poll_interval: float = 1.0
    keeper: bool = Field(False, description="Call advance() whenever a round can be advanced")

    # --- Protocol ---
    scheme: Scheme = Scheme.FHE
    attestation: Attestation = Attestation.ZK
    challenge_min: int = 10
    challenge_max: int = 9999

    # --- ZK ---
    zk_script: Path = Path("zk/zk.js")
    zk_build_dir: Path | None = None

    # --- FHE ---
    key_dir: Path = Path.home() / ".config" / "bbyor"

    # --- Simulation ---
    behaviour: Behaviour = Behaviour.HONEST
    fail_probability: float = 0.3
    attack_threshold: int = 600
    seed: int = 12

    # --- Metrics / logging ---
    metrics_file: Path = Path("metrics.jsonl")
    log_level: str = "INFO"
