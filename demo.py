"""
DataShield AI — End-to-End Live Demonstration Runner
=====================================================
Executes two simulated breach scenarios:
  [Scenario 1] High-Volume Behavioral Anomaly (ML Detection + Groq LLM + Blockchain)
  [Scenario 2] Honey Token Trap Sprung — Physical Cryptographic Proof of Theft
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is in python path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from api.services.detection_service import DetectionService
from api.services.report_service import ReportService
from api.services.blockchain_service import BlockchainService


def run_demo():
    print("\n" + "=" * 78)
    print("🛡️   DATASHIELD AI — ADVANCED BREACH PREVENTION & HONEY TOKEN FORENSICS")
    print("     Blockchain + Machine Learning + Groq LLM (openai/gpt-oss-120b)")
    print("=" * 78)

    # 1. Initialize Services
    print("\n[INIT] Initializing 3-layer architecture services & Honey Token Manager...")
    detection_svc = DetectionService()
    report_svc = ReportService()
    blockchain_svc = BlockchainService()

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 1: Machine Learning Behavioral Anomaly Detection
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "#" * 78)
    print("⚡ SCENARIO 1: AFTER-HOURS HIGH-VOLUME FOREIGN EXFILTRATION")
    print("#" * 78)

    incident_1 = {
        "event_id": "EVT-ANOMALY-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": "contractor_sec_04",
        "user_email": "dmitri.v@external-partner.com",
        "user_role": "contractor",
        "department": "Infrastructure Ops",
        "action": "EXPORT",
        "table_name": "prod.users",
        "columns_accessed": ["id", "email", "phone", "address"],
        "num_rows_affected": 85000,
        "source_ip": "185.220.101.5",
        "geo_location": "Bucharest, Romania",
        "session_duration_seconds": 45,
        "is_vpn": True,
    }

    print(f"\n📡 [DB Telemetry] User '{incident_1['user_id']}' EXPORT {incident_1['num_rows_affected']:,} rows from '{incident_1['table_name']}' via VPN.")
    det_1 = detection_svc.analyze_event(incident_1)
    print(f"🔍 [Layer 1 ML] Threat Score: {det_1['threat_score']}/100 [{det_1['threat_level']}] (IsolationForest + Autoencoder + LSTM)")
    for f in det_1.get("contributing_factors", [])[:2]:
        print(f"   ⚠️  {f}")

    rep_1 = report_svc.generate_report(event_data={**incident_1, **det_1}, threat_score=det_1['threat_score'], threat_level=det_1['threat_level'])
    print(f"🧠 [Layer 2 GenAI] Generator: {rep_1.get('generator')} | Executive Brief:")
    print(f"   \"{rep_1['executive_summary']}\"")

    bc_1 = blockchain_svc.log_event(incident_1, int(det_1['threat_score']), rep_1['full_report'][:64])
    print(f"⛓️ [Layer 3 Chain] Event Keccak-256: {bc_1['event_hash'][:22]}... | Tx: {bc_1['tx_hash'][:22]}... | Status: {bc_1['status']}")

    # ─────────────────────────────────────────────────────────────────────────
    # SCENARIO 2: Honey Token Decoy Tripwire & Physical Proof of Theft
    # ─────────────────────────────────────────────────────────────────────────
    print("\n" + "#" * 78)
    print("🪤 SCENARIO 2: HONEY TOKEN TRAP SPRUNG — IRREFUTABLE PROOF OF THEFT")
    print("#" * 78)

    incident_2 = {
        "event_id": "EVT-CANARY-TRAP-909",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": "insider_contractor_99",
        "user_email": "viktor.k@corp-partners.io",
        "user_role": "contractor",
        "department": "Data Pipeline",
        "action": "EXPORT",
        "table_name": "prod.credit_cards",
        "columns_accessed": ["cardholder_name", "credit_card", "cvv", "CANARY-CC-8821"],
        "num_rows_affected": 2500,
        "source_ip": "194.26.29.112",
        "geo_location": "Geneva, Switzerland",
        "session_duration_seconds": 30,
        "is_vpn": True,
    }

    print(f"\n📡 [DB Telemetry] User '{incident_2['user_id']}' queried '{incident_2['table_name']}' requesting Decoy Token 'CANARY-CC-8821'...")
    det_2 = detection_svc.analyze_event(incident_2)

    print(f"\n🚨 [TRIPWIRE TRIGGERED] Threat Score: {det_2['threat_score']}/100 [{det_2['threat_level']}]")
    print(f"   ► Decoy Status: HONEY TOKEN COMPROMISED (Canary: CANARY-CC-8821)")
    for f in det_2.get("contributing_factors", [])[:3]:
        print(f"   ► {f}")

    proof = det_2.get("proof_of_theft")
    if proof:
        print("\n📜 [CRYPTOGRAPHIC PROOF OF THEFT CERTIFICATE]")
        print(f"   • Certificate ID:          {proof['certificate_id']}")
        print(f"   • Mathematical Verdict:    {proof['verdict']} ({proof['confidence_ratio']})")
        print(f"   • Attributed Culprit:      {proof['suspect_identity']}")
        print(f"   • Planted Canary Asset:    {proof['canary_token_id']} in `{proof['target_schema']}`")
        print(f"   • Cryptographic Watermark: {proof['watermark_hash']}")
        print(f"   • Theft Digital Signature: {proof['cryptographic_proof_signature']}")
        print(f"   • Legal Admissibility:     {proof['chain_of_custody']['legal_admissibility']}")
        print(f"   • Forensic Finding:        \"{proof['forensic_summary']}\"")

    rep_2 = report_svc.generate_report(
        event_data={**incident_2, **det_2},
        threat_score=det_2['threat_score'],
        threat_level=det_2['threat_level'],
    )
    print(f"\n🧠 [GenAI Explainability] Active Engine: {rep_2.get('generator')}")
    print(f"   ► Executive Forensic Attestation:")
    print(f"     \"{rep_2['executive_summary']}\"")
    print("   ► Zero-Tolerance Containment Directives:")
    for i, a in enumerate(rep_2.get("recommended_actions", [])[:3], 1):
        print(f"     [{i}] {a}")

    # Anchor the proof of theft to Polygon Smart Contract
    chain_proof = blockchain_svc.trip_honeytoken_on_chain(
        token_id="CANARY-CC-8821",
        suspect_user_id=incident_2["user_id"],
        proof_certificate=proof,
    )
    print("\n⛓️ [SMART CONTRACT HONEY TOKEN EVIDENCE FREEZE]")
    print(f"   ► Status:             {chain_proof['status']} (IMMUTABLE EVIDENCE LOCKED)")
    print(f"   ► On-Chain Token Hash: {chain_proof['token_hash']}")
    print(f"   ► Smart Contract Tx:  {chain_proof['tx_hash']}")
    print(f"   ► IPFS Proof CID:     {chain_proof['proof_ipfs_cid']}")
    print(f"   ► Ledger Block:       #{chain_proof['block_number']}")

    print("\n" + "=" * 78)
    print("✅  HONEY TOKEN VERIFICATION & CRYPTOGRAPHIC THEFT PROOF COMPLETE")
    print("     The insider was lured by the planted canary, caught red-handed,")
    print("     and mathematical proof was minted forever on the blockchain.")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    run_demo()
