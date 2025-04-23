import os
from pathlib import Path
import logging
from typing import Optional, Tuple
from ..services.fhe import genKey, serializeKeyToFile
from ..services.connections import missing_conn, doConnections
from .settings import settings


logger = logging.getLogger(__name__)

def provision() -> Optional[Tuple[Path, Path]]:
    """
    Idempotent provisioning:
    1. Creates config directory if missing.
    2. Generates FHE keys only if they don't exist.
    
    Returns:
        Tuple of (public_key_path, secret_key_path) if keys were generated, else None.
    """    
    try:
        # Establish connections        
        doConnections(missing_conn())
        # Create FHE keys
        # Convert to Path objects (more robust than string paths)
        config_dir = Path(settings.DEFAULT_DIR)
        pk_path = config_dir / "pk.bin"
        sk_path = config_dir / "sk.bin"
        
        # 1. Create config directory (if not exists)                
        basedir = Path(settings.HOME+"/.config")        
        # create basedir
        basedir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Config directory: {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
        # 2. Generate keys ONLY if neither file exists
        if not (pk_path.exists() and sk_path.exists()):
            keypair = genKey()
            serializeKeyToFile(str(pk_path), keypair.publicKey)
            serializeKeyToFile(str(sk_path), keypair.secretKey)
            
            # Set restrictive permissions (600 for secrets)
            sk_path.chmod(0o600)
            logger.info("Generated new FHE keypair")
            return pk_path, sk_path
        else:
            logger.info("FHE keys already exist, skipping generation")
            return None                
    except Exception as e:
        logger.critical(f"Provisioning failed: {e}", exc_info=True)
        raise RuntimeError("Provisioning aborted") from e
    
  