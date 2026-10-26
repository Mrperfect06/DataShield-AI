"""
DataShield AI — Blockchain Client (Python / web3.py)

Provides a high-level Python interface to the deployed DataShieldAudit smart
contract.  Used by the API layer and orchestrator to log access events,
create / resolve threat alerts, and query audit data from the chain.

The client degrades gracefully when the blockchain node or contract is
unavailable — every public method catches connection errors and returns a
sensible fallback so that the rest of the pipeline is not blocked.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Project imports (best-effort) ────────────────────────────────────────────
try:
    # When running from the project root, config.py is importable directly.
    from config import (
        BLOCKCHAIN_DIR,
        CONTRACT_ADDRESS,
        DEPLOYER_PRIVATE_KEY,
        POLYGON_RPC_URL,
    )
except ImportError:
    # Fallback: derive paths & values from env / defaults so the module stays
    # usable even when config.py is not on sys.path.
    BLOCKCHAIN_DIR = Path(__file__).parent
    POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "http://127.0.0.1:8545")
    DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY", "")
    CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")

# ── web3.py (optional dependency) ────────────────────────────────────────────
try:
    from web3 import Web3
    from web3.exceptions import ContractLogicError

    WEB3_AVAILABLE = True
except ImportError:
    WEB3_AVAILABLE = False

logger = logging.getLogger("datashield.blockchain")


# ─────────────────────────────────────────────────────────────────────────────
#  Helper: load ABI
# ─────────────────────────────────────────────────────────────────────────────

def _load_abi(abi_path: Path) -> Optional[list]:
    """Load the contract ABI from *abi_path*.

    Returns ``None`` when the file does not exist or is malformed, allowing
    the caller to decide whether to abort or fall back.
    """
    if not abi_path.exists():
        logger.warning("ABI file not found at %s — contract calls disabled.", abi_path)
        return None
    try:
        with open(abi_path, "r", encoding="utf-8") as fh:
            abi = json.load(fh)
        if not isinstance(abi, list):
            logger.warning("ABI file at %s is not a JSON array.", abi_path)
            return None
        return abi
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to read ABI file at %s: %s", abi_path, exc)
        return None


def _load_contract_address() -> str:
    """Return the deployed contract address.

    Priority:
      1. ``CONTRACT_ADDRESS`` from config / env
      2. ``deployment.json`` in the blockchain directory
    """
    if CONTRACT_ADDRESS:
        return CONTRACT_ADDRESS

    deployment_file = Path(BLOCKCHAIN_DIR) / "deployment.json"
    if deployment_file.exists():
        try:
            with open(deployment_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            addr = data.get("address", "")
            if addr:
                logger.info("Loaded contract address from deployment.json: %s", addr)
                return addr
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read deployment.json: %s", exc)
    return ""


# ─────────────────────────────────────────────────────────────────────────────
#  BlockchainClient
# ─────────────────────────────────────────────────────────────────────────────

class BlockchainClient:
    """High-level Python wrapper around the DataShieldAudit smart contract.

    Parameters
    ----------
    rpc_url : str, optional
        JSON-RPC endpoint of the EVM node.  Defaults to the value in config.py.
    contract_address : str, optional
        Hex address of the deployed contract.  Auto-detected from
        ``deployment.json`` when omitted.
    abi_path : str or Path, optional
        Path to the ABI JSON array.  Defaults to ``blockchain/abi.json``.
    private_key : str, optional
        Deployer / signer private key (hex string).  Defaults to the value
        in config.py (which itself falls back to the Hardhat account #0).
    """

    # ── construction ─────────────────────────────────────────────────────

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        contract_address: Optional[str] = None,
        abi_path: Optional[str] = None,
        private_key: Optional[str] = None,
    ) -> None:
        self.rpc_url: str = rpc_url or POLYGON_RPC_URL
        self.private_key: str = private_key or DEPLOYER_PRIVATE_KEY
        self.connected: bool = False
        self.w3: Optional[Any] = None
        self.contract: Optional[Any] = None
        self.account: Optional[Any] = None

        if not WEB3_AVAILABLE:
            logger.warning(
                "web3 package is not installed — blockchain features disabled. "
                "Install with: pip install web3"
            )
            return

        # Resolve ABI path
        _abi_path = Path(abi_path) if abi_path else Path(BLOCKCHAIN_DIR) / "abi.json"
        abi = _load_abi(_abi_path)
        if abi is None:
            logger.warning("No valid ABI available; blockchain features disabled.")
            return

        # Resolve contract address
        _address = contract_address or _load_contract_address()
        if not _address:
            logger.warning(
                "Contract address is not set — deploy the contract first."
            )
            return

        # Connect to the node
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self.w3.is_connected():
                logger.warning(
                    "Unable to connect to blockchain node at %s", self.rpc_url
                )
                return

            self.account = self.w3.eth.account.from_key(self.private_key)
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(_address),
                abi=abi,
            )
            self.connected = True
            logger.info(
                "BlockchainClient connected — node=%s  contract=%s  signer=%s",
                self.rpc_url,
                _address,
                self.account.address,
            )
        except Exception as exc:
            logger.error("Failed to initialise BlockchainClient: %s", exc)
            self.connected = False

    # ── internal helpers ─────────────────────────────────────────────────

    def _require_connection(self) -> bool:
        """Return True when the client is operational, False otherwise."""
        if not self.connected:
            logger.warning("BlockchainClient is not connected — skipping call.")
            return False
        return True

    def _send_tx(self, fn) -> Optional[str]:
        """Build, sign, and send a contract-write transaction.

        Parameters
        ----------
        fn : ContractFunction
            A bound contract function produced by
            ``self.contract.functions.<method>(...)``.

        Returns
        -------
        str or None
            The hex-encoded transaction hash, or ``None`` on failure.
        """
        try:
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            tx = fn.build_transaction(
                {
                    "from": self.account.address,
                    "nonce": nonce,
                    "gas": 500_000,
                    "gasPrice": self.w3.eth.gas_price,
                }
            )
            signed = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            hex_hash = receipt.transactionHash.hex()
            logger.info("Transaction mined — hash=%s  status=%s", hex_hash, receipt.status)
            return hex_hash
        except ContractLogicError as exc:
            logger.error("Contract reverted: %s", exc)
            return None
        except Exception as exc:
            logger.error("Transaction failed: %s", exc)
            return None

    # ── write methods ────────────────────────────────────────────────────

    def log_access_event(
        self,
        event_hash: bytes,
        user_id: str,
        action: str,
        table_name: str,
        threat_score: int,
        ipfs_hash: str = "",
    ) -> Optional[str]:
        """Log an access event on-chain.

        Parameters
        ----------
        event_hash : bytes
            32-byte keccak-256 hash identifying the event.
        user_id : str
            Database user who performed the action.
        action : str
            SQL action type (SELECT, DELETE, etc.).
        table_name : str
            Fully-qualified table name.
        threat_score : int
            ML-assigned score in 0–100.
        ipfs_hash : str
            IPFS CID of the full GenAI report (may be empty).

        Returns
        -------
        str or None
            Transaction hash on success, ``None`` on failure.
        """
        if not self._require_connection():
            return None

        fn = self.contract.functions.logAccessEvent(
            event_hash, user_id, action, table_name, threat_score, ipfs_hash
        )
        return self._send_tx(fn)

    def create_threat_alert(
        self, event_hash: bytes, threat_level: str
    ) -> Optional[str]:
        """Manually create a threat alert for an existing event.

        Parameters
        ----------
        event_hash : bytes
            Hash of a previously logged event.
        threat_level : str
            Severity label (LOW, MEDIUM, HIGH, CRITICAL).

        Returns
        -------
        str or None
            Transaction hash on success.
        """
        if not self._require_connection():
            return None

        fn = self.contract.functions.createThreatAlert(event_hash, threat_level)
        return self._send_tx(fn)

    def resolve_alert(self, alert_id: int) -> Optional[str]:
        """Mark an alert as resolved.

        Parameters
        ----------
        alert_id : int
            The on-chain alert ID.

        Returns
        -------
        str or None
            Transaction hash on success.
        """
        if not self._require_connection():
            return None

        fn = self.contract.functions.resolveAlert(alert_id)
        return self._send_tx(fn)

    # ── read methods ─────────────────────────────────────────────────────

    def get_access_event(self, event_hash: bytes) -> Optional[Dict[str, Any]]:
        """Retrieve a single access event from the chain.

        Returns
        -------
        dict or None
            A dictionary with keys matching the ``AccessEvent`` struct, or
            ``None`` when the client is disconnected or the event is missing.
        """
        if not self._require_connection():
            return None
        try:
            result = self.contract.functions.getAccessEvent(event_hash).call()
            return self._parse_access_event(result)
        except ContractLogicError as exc:
            logger.error("getAccessEvent reverted: %s", exc)
            return None
        except Exception as exc:
            logger.error("getAccessEvent failed: %s", exc)
            return None

    def get_threat_alert(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single threat alert.

        Returns
        -------
        dict or None
        """
        if not self._require_connection():
            return None
        try:
            result = self.contract.functions.getThreatAlert(alert_id).call()
            return self._parse_threat_alert(result)
        except ContractLogicError as exc:
            logger.error("getThreatAlert reverted: %s", exc)
            return None
        except Exception as exc:
            logger.error("getThreatAlert failed: %s", exc)
            return None

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Fetch every logged access event.

        Returns
        -------
        list[dict]
            A list of event dictionaries; empty if disconnected.
        """
        if not self._require_connection():
            return []
        try:
            hashes = self.contract.functions.getAllEventHashes().call()
            events: List[Dict[str, Any]] = []
            for h in hashes:
                raw = self.contract.functions.getAccessEvent(h).call()
                events.append(self._parse_access_event(raw))
            return events
        except Exception as exc:
            logger.error("get_all_events failed: %s", exc)
            return []

    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """Fetch every threat alert (resolved and unresolved).

        Returns
        -------
        list[dict]
        """
        if not self._require_connection():
            return []
        try:
            ids = self.contract.functions.getAllAlertIds().call()
            alerts: List[Dict[str, Any]] = []
            for aid in ids:
                raw = self.contract.functions.getThreatAlert(aid).call()
                alerts.append(self._parse_threat_alert(raw))
            return alerts
        except Exception as exc:
            logger.error("get_all_alerts failed: %s", exc)
            return []

    def get_unresolved_alerts(self) -> List[Dict[str, Any]]:
        """Fetch all unresolved threat alerts.

        Returns
        -------
        list[dict]
        """
        if not self._require_connection():
            return []
        try:
            raw_list = self.contract.functions.getUnresolvedAlerts().call()
            return [self._parse_threat_alert(r) for r in raw_list]
        except Exception as exc:
            logger.error("get_unresolved_alerts failed: %s", exc)
            return []

    def get_event_count(self) -> int:
        """Return the total number of logged access events."""
        if not self._require_connection():
            return 0
        try:
            return self.contract.functions.getEventCount().call()
        except Exception as exc:
            logger.error("get_event_count failed: %s", exc)
            return 0

    def get_alert_count(self) -> int:
        """Return the total number of alerts."""
        if not self._require_connection():
            return 0
        try:
            return self.contract.functions.getAlertCount().call()
        except Exception as exc:
            logger.error("get_alert_count failed: %s", exc)
            return 0

    # ── static / utility ─────────────────────────────────────────────────

    @staticmethod
    def compute_event_hash(event_data: dict) -> bytes:
        """Compute a deterministic keccak-256 hash for an event.

        The event dictionary is serialised to a canonical JSON string
        (sorted keys, no whitespace) before hashing — matching the approach
        used by the ML pipeline and the orchestrator.

        Parameters
        ----------
        event_data : dict
            Arbitrary event payload.

        Returns
        -------
        bytes
            32-byte hash suitable for passing to ``log_access_event``.
        """
        canonical = json.dumps(event_data, sort_keys=True, separators=(",", ":"))
        if WEB3_AVAILABLE:
            return Web3.keccak(text=canonical)
        # Fallback when web3 is not installed: use hashlib
        return hashlib.sha3_256(canonical.encode("utf-8")).digest()

    # ── private parsers ──────────────────────────────────────────────────

    @staticmethod
    def _parse_access_event(raw) -> Dict[str, Any]:
        """Convert a contract return tuple into a Python dict.

        The Solidity struct ``AccessEvent`` is returned as a tuple ordered:
          (eventHash, timestamp, userId, action, tableName, threatScore, ipfsReportHash)
        """
        return {
            "event_hash": raw[0].hex() if isinstance(raw[0], bytes) else raw[0],
            "timestamp": int(raw[1]),
            "user_id": raw[2],
            "action": raw[3],
            "table_name": raw[4],
            "threat_score": int(raw[5]),
            "ipfs_report_hash": raw[6],
        }

    @staticmethod
    def _parse_threat_alert(raw) -> Dict[str, Any]:
        """Convert a contract return tuple into a Python dict.

        The Solidity struct ``ThreatAlert`` is returned as a tuple ordered:
          (alertId, eventHash, threatLevel, timestamp, responderAddress, resolved)
        """
        return {
            "alert_id": int(raw[0]),
            "event_hash": raw[1].hex() if isinstance(raw[1], bytes) else raw[1],
            "threat_level": raw[2],
            "timestamp": int(raw[3]),
            "responder_address": raw[4],
            "resolved": bool(raw[5]),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Module-level convenience: importable singleton
# ─────────────────────────────────────────────────────────────────────────────

def get_blockchain_client(**kwargs) -> BlockchainClient:
    """Factory function that creates a ``BlockchainClient`` with project defaults.

    Any keyword argument is forwarded to the constructor, overriding the
    corresponding config value.  Example::

        client = get_blockchain_client(rpc_url="http://localhost:8545")
    """
    return BlockchainClient(**kwargs)


# ─────────────────────────────────────────────────────────────────────────────
#  Quick self-test (python blockchain/blockchain_client.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    client = get_blockchain_client()

    if not client.connected:
        print(
            "\n⚠  Blockchain client could not connect.\n"
            "   Make sure a local Hardhat node is running (npx hardhat node)\n"
            "   and the contract has been deployed (npm run deploy:local).\n"
        )
        sys.exit(0)

    print(f"\n✅  Connected to blockchain at {client.rpc_url}")
    print(f"   Contract address : {client.contract.address}")
    print(f"   Signer address   : {client.account.address}")
    print(f"   Event count      : {client.get_event_count()}")
    print(f"   Alert count      : {client.get_alert_count()}")
    print()
