from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, DirectoryPath, FilePath
from typing import Optional
import os

class Settings(BaseSettings):
    # --- Agent Configuration ---
    ACAPY_URL: str = Field(
        default="http://localhost:8445",
        description="ACA-Py Admin API URL",
        env="ACAPY_URL"
    )
    CONNECTIONS_URL: str = "/connections"
    DID_EXCHANGE_ENDPOINT: str = "/didexchange/create-request?their_public_did="

    # ----- Logging --------
    LOG_LEVEL: Optional[str] = Field(
        default=os.getenv("LOG_LEVEL", "DEBUG"),
        description="User home directory",
        env="LOG_LEVEL"
    )
    LOG_FILE: Optional[str] = Field(
        default=os.getenv("LOG_FILE"),
        description="User home directory",        
    )

    # --- Paths ---
    HOME: Optional[str] = Field(
        default=os.getenv("HOME"),
        description="User home directory",
        env="HOME"
    )
    DEFAULT_DIR: str = Field(
        default=f"{os.getenv('HOME', '/tmp')}/.config/bbyor",
        description="Default config directory",
        env="DEFAULT_DIR"
    )

    # --- Blockchain ---
    PROVIDER_URL: str = Field(
        default="http://localhost:8545",
        env="PROVIDER_URL"
    )
    GENESIS_FHE: str = Field(
        default="../contracts/genesis_openfhe.json",
        description="Path to Genesis FHE file"
    )
    CONTRACT_ADDR: str = Field(
        default="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        env="CONTRACT_ADDR"
    )
    PRIVATE_KEY: str = Field(
        default="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
        env="PRIVATE_KEY"
    )
    CONTRACT_ABI_PATH: FilePath = Field(
        default="./contracts/artifacts/abi.json",
        description="Path to contract ABI file"
    )

    # --- Dynamic Defaults and Validation ---
    @field_validator("DEFAULT_DIR", mode="before")
    def set_default_dir(cls, v, values):
        return v or f"{values.data.get('HOME', '/tmp')}/.config/bbyor"

    @field_validator("CONTRACT_ABI_PATH", mode="before")
    def validate_abi_path(cls, v):
        if not os.path.exists(v):
            raise FileNotFoundError(f"ABI file not found at {v}")
        return v

    # --- Pydantic Config ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )

# Singleton instance
settings = Settings()