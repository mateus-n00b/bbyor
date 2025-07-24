import json
import requests as rq
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config.settings import settings
from ..utils.logging import get_logger
from ..contracts.client import contract_client
import time

logger = get_logger()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    before_sleep=lambda _: logger.warning("Retrying failed connection check...")
)
def get_connections() -> Optional[dict]:
    """Fetch connections with retry logic"""
    try:
        response = rq.get(
            f"{settings.ACAPY_URL}{settings.CONNECTIONS_URL}",
            timeout=5
        )
        if response.status_code != 200:
            logger.error(f"Unexpected status: {response.status_code}, Response: {response.text}")
            return None
        return response.json()
    except Exception as e:
        logger.error(f"Connection check failed: {str(e)}")
        raise

def missing_conn() -> List[str]:   
    """Identify missing connections with proper error handling"""
    try:
        with open(settings.GENESIS_FHE) as f:
            peers = json.load(f)    
            connections_data = get_connections()
            if not connections_data:
                return []
                
            existing_connections = [conn.get("their_public_did") for conn in connections_data.get("results", [])]
            return [peer for peer in peers if peer not in existing_connections and peer != settings.PUBLIC_DID]
        
    except Exception as e:
        logger.critical(f"Failed to check missing connections: {str(e)}")
        return []


def get_public_did():
    response = rq.get(
            f"{settings.ACAPY_URL}{settings.WALLET_PUBLIC_DID}",
            timeout=10
        )
    if response.status_code == 200:
        logger.info(f"DID recovered")
        result = response.json()["result"]
        return result["did"]
    return None

@retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=2, max=5)
)
def establish_connection(did: str) -> bool:
    """Create connection with retry logic"""    
    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
            response = rq.post(
                f"{settings.ACAPY_URL}{settings.DID_EXCHANGE_ENDPOINT.format(did)}",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully initiated connection with {did}")
                results = response.json()
                conn_id = results["connection_id"]
                return conn_id
                
            logger.warning(
                f"Unexpected response for {did}: "
                f"Status={response.status_code}, Response={response.text}"
            )
            return False
            
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2)  # Wait before retrying
            else:
                logger.error(f"Failed to connect to {did}: {str(e)}")
                raise

def handle_connections() -> dict:
    """
    Main workflow with proper status handling
    Returns:
        {
            "success": List[str],  # DIDs with successful connection init
            "failed": List[str],   # DIDs that failed
            "skipped": List[str]   # Already connected peers
        }
    """
    # if not peers:
    #     return {"success": [], "failed": [], "skipped": []}
    
    missing = missing_conn()
    if not missing:
        logger.info("All peers are already connected")
        return {"success": [], "failed": []}
    
    results = {"success": [], "failed": []}
    
    for did in missing:
        if establish_connection(did):
            results["success"].append(did)   
            # register neighbors
            contract_client.register_neighbor(did)
        else:
            results["failed"].append(did)
    
    logger.info(
        f"Connection results: {len(results['success'])} succeeded, "
        f"{len(results['failed'])} failed")
    return results

def send_message(connection_id: str, message: dict):
    message_json = json.dumps(message)
    url = settings.ACAPY_URL + settings.BASIC_MESSAGE_URI.format(connection_id)

    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
            response = rq.post(url, json={"content": message_json})
            response.raise_for_status()  # Raises HTTPError on bad responses
            return  # Success
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2)  # Wait before retrying
            else:
                print("All retry attempts failed.")
                raise  # Re-raise the last exception after final attempt
