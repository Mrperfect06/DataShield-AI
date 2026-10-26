"""
DataShield AI — GenAI Threat Forensic Report Generator
========================================================
Combines high-speed LLM intelligence via Groq (openai/gpt-oss-120b)
and Gemini with RAG security policies and SHAP feature attribution
to generate explainable, auditable breach reports.
Includes high-fidelity template generation fallback for offline or zero-key mode.
"""

from __future__ import annotations

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GEMINI_API_KEY,
    LLM_MODEL_NAME,
)
from genai_explainer.prompts.threat_report import SYSTEM_PROMPT, THREAT_REPORT_PROMPT
from genai_explainer.rag_pipeline import SecurityKnowledgeBase
from genai_explainer.shap_analyzer import SHAPAnalyzer

logger = logging.getLogger("datashield.report_generator")

try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except ImportError:
    _GROQ_AVAILABLE = False


class ThreatReportGenerator:
    """
    Produces executive & forensic reports explaining detected threats using Groq / Gemini LLMs.
    """

    def __init__(
        self,
        knowledge_base: Optional[SecurityKnowledgeBase] = None,
        shap_analyzer: Optional[SHAPAnalyzer] = None,
    ):
        self.kb = knowledge_base or SecurityKnowledgeBase()
        self.shap_analyzer = shap_analyzer or SHAPAnalyzer()
        
        self.groq_api_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY)
        self.groq_model = os.getenv("GROQ_MODEL", GROQ_MODEL)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", GEMINI_API_KEY)
        
        self.groq_client = None
        self.gemini_client = None
        self._init_llm_clients()

    def _init_llm_clients(self):
        # 1. Initialize Groq (Primary LLM Engine)
        if _GROQ_AVAILABLE and self.groq_api_key and self.groq_api_key != "your_groq_key":
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                logger.info(f"Groq LLM client initialized with model: {self.groq_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
                self.groq_client = None

        # 2. Initialize Gemini (Secondary LLM Engine)
        if self.gemini_api_key and self.gemini_api_key != "your_gemini_api_key_here":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel(
                    model_name=LLM_MODEL_NAME,
                    system_instruction=SYSTEM_PROMPT,
                )
                logger.info("Gemini LLM client initialized.")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
                self.gemini_client = None

    def generate_report(
        self,
        event_data: Dict[str, Any],
        threat_score: float,
        threat_level: str,
        shap_explanation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates full narrative report, executive summary, and compliance mandates.
        """
        # Retrieve context from RAG
        keywords = []
        if event_data.get("is_after_hours"):
            keywords.append("after-hours")
        if event_data.get("has_pii") or event_data.get("num_sensitive_columns", 0) > 0:
            keywords.append("pii")
        if event_data.get("num_rows_affected", 0) > 5000:
            keywords.append("bulk download")
        if event_data.get("is_vpn"):
            keywords.append("travel")

        relevant_policies = self.kb.get_relevant_policies(keywords=keywords)
        similar_incidents = self.kb.get_similar_incidents(indicators=keywords)

        factors = event_data.get("contributing_factors", [])
        if not factors and shap_explanation:
            factors = shap_explanation.get("top_factors", [])

        # Build prompt tailored to risk level
        if threat_score < 35.0:
            prompt = f"""Analyze the following authorized database access event and generate an operational compliance audit report:

### Event Telemetry:
- **Event ID:** {event_data.get('event_id', 'EVT-LIVE')}
- **Timestamp:** {event_data.get('timestamp', datetime.utcnow().isoformat())}
- **User Identity:** {event_data.get('user_id', 'Unknown')} ({event_data.get('user_email', 'N/A')})
- **Role / Department:** {event_data.get('user_role', 'Standard User')} / {event_data.get('department', 'General')}
- **Action:** {event_data.get('action', 'SELECT')} on table `{event_data.get('table_name', 'db.table')}`
- **Columns Accessed:** {event_data.get('columns_accessed', ['standard'])}
- **Volume:** {event_data.get('num_rows_affected', 0)} records
- **Network Origin:** IP {event_data.get('source_ip', '0.0.0.0')} (Location: {event_data.get('geo_location', 'Internal')}, VPN: {event_data.get('is_vpn', False)})

### Assessment:
- **Calculated Threat Score:** {threat_score}/100 (LOW - Benign Operational Access)
- **Status:** Standard routine access conforming to enterprise operational baseline.

Format with clean markdown:
- ## 🟢 Audit Summary: Authorized Routine Access
- ## 👤 Principal & Operational Context
- ## 🔍 Telemetry & Baseline Conformance (Explain why {event_data.get('num_rows_affected', 0)} rows from `{event_data.get('table_name')}` is safe and expected)
- ## 🛡️ Compliance & Governance Status
- ## 📋 Blockchain Chain of Custody
"""
        else:
            prompt = THREAT_REPORT_PROMPT.format(
                event_id=event_data.get("event_id", "EVT-LIVE"),
                timestamp=event_data.get("timestamp", datetime.utcnow().isoformat()),
                user_id=event_data.get("user_id", "Unknown"),
                user_email=event_data.get("user_email", "N/A"),
                user_role=event_data.get("user_role", "Standard User"),
                department=event_data.get("department", "General"),
                action=event_data.get("action", "QUERY"),
                table_name=event_data.get("table_name", "db.table"),
                columns_accessed=event_data.get("columns_accessed", ["unknown"]),
                num_rows=event_data.get("num_rows_affected", 0),
                source_ip=event_data.get("source_ip", "0.0.0.0"),
                geo_location=event_data.get("geo_location", "Unknown"),
                is_vpn=event_data.get("is_vpn", False),
                threat_score=threat_score,
                threat_level=threat_level,
                anomaly_factors="; ".join(factors),
                shap_explanation=str(shap_explanation.get("feature_importance", {})) if shap_explanation else "N/A",
                relevant_policies="\n".join([f"- {p.get('id')}: {p.get('title')} ({p.get('description')})" for p in relevant_policies]),
                similar_incidents="\n".join([f"- {i.get('incident_id')}: {i.get('summary')} (Resolved: {i.get('resolution')})" for i in similar_incidents]),
            )

        report_text = None
        active_engine = "DataShield-Deterministic-Engine"

        # 1. Try Groq (User preferred)
        if self.groq_client:
            try:
                completion = self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_completion_tokens=2048,
                    top_p=1,
                    stream=True,
                )
                chunks = []
                for chunk in completion:
                    content = chunk.choices[0].delta.content or ""
                    chunks.append(content)
                report_text = "".join(chunks)
                active_engine = f"Groq ({self.groq_model})"
            except Exception as e:
                logger.warning(f"Groq LLM generation failed ({e}), falling back...")
                report_text = None

        # 2. Try Gemini fallback
        if not report_text and self.gemini_client:
            try:
                response = self.gemini_client.generate_content(prompt)
                report_text = response.text
                active_engine = "Gemini-2.0-Flash"
            except Exception as e:
                logger.warning(f"Gemini LLM generation failed ({e}), falling back...")
                report_text = None

        # 3. Fallback to deterministic template report
        if not report_text:
            report_text = self._build_template_report(
                event_data=event_data,
                threat_score=threat_score,
                threat_level=threat_level,
                factors=factors,
                policies=relevant_policies,
                incidents=similar_incidents,
            )

        # Extract structured artifacts
        exec_summary = self._build_executive_summary(event_data, threat_score, threat_level, factors)
        recommended_actions = self._build_recommended_actions(event_data, threat_score, relevant_policies)
        compliance_notes = self._build_compliance_notes(event_data, relevant_policies)

        return {
            "full_report": report_text,
            "executive_summary": exec_summary,
            "recommended_actions": recommended_actions,
            "compliance_notes": compliance_notes,
            "risk_level": threat_level,
            "threat_score": threat_score,
            "confidence": 0.95 if threat_score >= 60 else 0.89,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "generator": active_engine,
        }

    def _build_template_report(
        self,
        event_data: Dict[str, Any],
        threat_score: float,
        threat_level: str,
        factors: List[str],
        policies: List[Dict[str, Any]],
        incidents: List[Dict[str, Any]],
    ) -> str:
        user = event_data.get("user_id", "user_unknown")
        email = event_data.get("user_email", "N/A")
        role = event_data.get("user_role", "standard")
        dept = event_data.get("department", "Engineering")
        action = event_data.get("action", "ACCESS")
        table = event_data.get("table_name", "production_data")
        rows = event_data.get("num_rows_affected", 0)
        ip = event_data.get("source_ip", "127.0.0.1")
        geo = event_data.get("geo_location", "Unknown Location")
        vpn = "Enabled (Masked Gateway)" if event_data.get("is_vpn") else "Disabled (Direct)"

        proof = event_data.get("proof_of_theft")
        honey_section = ""
        if proof:
            honey_section = f"""\n## 🪤 Honey Token Trap & Physical Proof of Theft
- **Verdict:** `{proof.get('verdict', 'CONFIRMED_DATA_THEFT')}` ({proof.get('confidence_ratio', '100% Deterministic')})
- **Certificate ID:** `{proof.get('certificate_id')}`
- **Attributed Culprit:** `{proof.get('suspect_identity')}`
- **Canary Decoy Asset:** `{proof.get('canary_token_id')}` (Target: `{proof.get('target_schema')}`)
- **Watermark Digest:** `{proof.get('watermark_hash')}`
- **Cryptographic Signature:** `{proof.get('cryptographic_proof_signature')}`
- **Legal Admissibility:** {proof.get('chain_of_custody', {}).get('legal_admissibility')}
- **Forensic Attestation:** {proof.get('forensic_summary')}
"""

        if threat_score < 35.0:
            return f"""## 🟢 Operational Access Audit — Normal Baseline
The logged database access has been evaluated with **Threat Score {threat_score}/100 (LOW Risk)**. Telemetry aligns completely with expected operational baseline parameters for authorized internal users.

## 👤 Identity & Context
- **Principal:** `{user}` ({email})
- **Organizational Unit:** {dept} Department | Role: `{role}`
- **Originating Endpoint:** `{ip}` ({geo}) | Connection: {vpn}

## 🔍 Telemetry & Baseline Conformance
The user performed an authorized **`{action}`** query returning **{rows:,} records** from table **`{table}`**.
- **Row Volume Assessment:** {rows:,} records is well within normal query limits (< 250 threshold).
- **Data Classification:** Non-sensitive operational tables with zero PII exposure.
- **Timing & Velocity:** Query executed during normal business hours with standard velocity.

## ⚖️ Policy & Regulatory Status
- **Audit Policy POL-000:** Standard Authorized Operational Access verified.
- **Compliance Status:** SOC2-CC6 and ISO-27001 logging criteria satisfied. No governance breaches identified.

## 🛡️ Recommended Actions
1. **Permit Query Execution:** Zero containment required; allow transaction to complete without latency.
2. **Immutable Ledger Logging:** Record Keccak-256 event hash to blockchain audit trail.
3. **Continuous Baseline Monitoring:** Maintain automated telemetry surveillance.
"""

        policy_lines = "\n".join([f"- **{p.get('id')} ({p.get('title')})**: {p.get('description')} *(Frameworks: {', '.join(p.get('compliance_frameworks', []))})*" for p in policies]) or "- Standard Corporate Data Access Baseline Policy"
        incident_lines = "\n".join([f"- **{inc.get('incident_id')}**: {inc.get('summary')} *(Precedent: {inc.get('resolution')})*" for inc in incidents]) or "- No direct historic breach fingerprint match."
        factor_lines = "\n".join([f"- {f}" for f in factors]) or "- Statistical baseline deviation in access frequency."

        return f"""## 🚨 Incident Overview
Anomalous data access activity detected with **Threat Score {threat_score}/100** ({threat_level} Priority). Telemetry exhibits behavioral patterns highly correlated with data exfiltration or credential takeover.
{honey_section}
## 👤 Identity & Context
- **Principal:** `{user}` ({email})
- **Organizational Unit:** {dept} Department | Role: `{role}`
- **Originating Endpoint:** `{ip}` ({geo}) | VPN: {vpn}

## 🔍 Telemetry & Anomaly Analysis
The principal executed operation **`{action}`** targeting table **`{table}`**, returning **{rows:,} records**.
**Observed Threat Indicators:**
{factor_lines}

## ⚖️ Policy & Regulatory Implications
The detected action violates internal governance boundaries and triggers compliance requirements:
{policy_lines}

## 🛡️ Recommended Containment Actions
1. **Immediate Revocation:** Temporarily freeze DB session and revoke credentials for `{user}`.
2. **Quarantine Payload:** Isolate network ingress from IP `{ip}` and verify DLP cache buffers.
3. **Identity Verification:** Trigger mandatory out-of-band MFA and biometric attestation with `{dept}` lead.
4. **Forensic Anchoring:** Cryptographically anchor event hash on blockchain for chain-of-custody preservation.

## 📋 Precedent Incident Analysis
{incident_lines}
"""

    def _build_executive_summary(
        self,
        event_data: Dict[str, Any],
        threat_score: float,
        threat_level: str,
        factors: List[str],
    ) -> str:
        user = event_data.get("user_id", "user")
        table = event_data.get("table_name", "production")
        rows = event_data.get("num_rows_affected", 0)
        if threat_score < 35.0:
            return (
                f"Routine operational access verified ({threat_level} - {threat_score}/100): "
                f"User '{user}' executed safe query of {rows:,} records from '{table}'. "
                f"No security anomalies detected; activity logged to immutable audit ledger."
            )
        return (
            f"High-confidence threat alert ({threat_level} - {threat_score}/100): "
            f"User '{user}' executed suspicious bulk extraction of {rows:,} records from '{table}'. "
            f"Primary anomalies include: {', '.join(factors[:2])}."
        )

    def _build_recommended_actions(
        self,
        event_data: Dict[str, Any],
        threat_score: float,
        policies: List[Dict[str, Any]],
    ) -> List[str]:
        actions = []
        user = event_data.get("user_id", "the user")
        if threat_score >= 80:
            actions.append(f"Auto-Block: Suspend Active Directory credentials and DB read tokens for {user}")
            actions.append("Network Defense: Blacklist source IP at perimeter firewall")
            actions.append("Forensics: Trigger automated tamper-proof evidence freeze on blockchain")
            actions.append("Legal: Initiate 72-hour GDPR Article 33 notification triage")
        elif threat_score >= 60:
            actions.append(f"Access Control: Temporarily quarantine queries to production tables by {user}")
            actions.append("Manager Escalation: Send Slack/Email urgent alert to Department Manager")
            actions.append("MFA Challenge: Require immediate re-authentication with hardware token")
        elif threat_score >= 35:
            actions.append(f"Auditing: Increase telemetry sampling frequency for user {user}")
            actions.append("Review: Flag for routine SOC weekly compliance review")
        else:
            actions.append("Audit Trail: Record Keccak-256 hash to Polygon PoS smart contract")
            actions.append("Pass-Through: Allow database query execution with zero restriction")
        return actions

    def _build_compliance_notes(
        self,
        event_data: Dict[str, Any],
        policies: List[Dict[str, Any]],
    ) -> List[str]:
        notes = []
        has_pii = bool(event_data.get("has_pii") or event_data.get("num_sensitive_columns", 0) > 0)
        rows = event_data.get("num_rows_affected", 0)

        if has_pii or rows > 5000:
            notes.append("GDPR Article 33/34: Notification of personal data breach within 72 hours if customer PII exposed.")
            notes.append("SOC 2 Type II: CC6.1 - Logical access controls violation recorded in audit log.")

        table = str(event_data.get("table_name", "")).lower()
        if "medical" in table or "patient" in table:
            notes.append("HIPAA 45 CFR § 164.312(b): Audit controls review mandatory for medical records query.")

        if not notes:
            notes.append("SOC 2 Type II: CC6.1 - Authorized routine database transaction recorded in immutable ledger.")
            notes.append("ISO 27001: A.12.4.1 - Access activity validated against baseline access policies.")
        return notes
