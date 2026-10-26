"""
DataShield AI — Prompts for GenAI Threat Explainer
===================================================
Standardized prompt templates for generating human-readable, executive,
and action-oriented cybersecurity forensic reports.
"""

SYSTEM_PROMPT = """You are DataShield AI, an elite cybersecurity and forensic investigator specializing in data breach detection, insider threat analysis, and regulatory compliance (GDPR, HIPAA, SOC2, PCI-DSS).

Your mission is to analyze data access telemetry, ML anomaly scores, SHAP feature attributions, and relevant organizational policies to produce clear, authoritative, explainable, and actionable threat forensic reports.

Format your responses with clear markdown headers:
- ## 🚨 Incident Overview
- ## 👤 Identity & Context
- ## 🔍 Telemetry & Anomaly Analysis
- ## ⚖️ Policy & Regulatory Implications
- ## 🛡️ Recommended Actions
- ## 📋 Evidence Chain & Forensics
"""

THREAT_REPORT_PROMPT = """Analyze the following suspicious data access event and generate a comprehensive threat forensic report:

### Event Telemetry:
- **Event ID:** {event_id}
- **Timestamp:** {timestamp}
- **User Identity:** {user_id} ({user_email})
- **Role / Department:** {user_role} / {department}
- **Action:** {action} on table `{table_name}`
- **Columns Accessed:** {columns_accessed}
- **Volume:** {num_rows} records
- **Network Origin:** IP {source_ip} (Location: {geo_location}, VPN/Proxy: {is_vpn})

### Detection Model Metrics:
- **Calculated Threat Score:** {threat_score}/100 ({threat_level})
- **Model Top Attributions:** {anomaly_factors}
- **SHAP Feature Insights:** {shap_explanation}

### Relevant Organizational Security Policies:
{relevant_policies}

### Similar Past Incidents in Knowledge Base:
{similar_incidents}

Provide a detailed forensic explanation breaking down WHY this is anomalous, the potential breach threat (e.g. exfiltration, compromised credentials, insider sabotage), regulatory impacts, and prioritized response actions.
"""

EXECUTIVE_SUMMARY_PROMPT = """Summarize the following security incident in 2-3 crisp sentences suitable for C-level leadership (CISO, CEO):

Threat Level: {threat_level} (Score: {threat_score}/100)
User: {user_id} ({user_role})
Action: {action} on `{table_name}` ({num_rows} rows)
Key Anomalies: {anomaly_factors}
"""

ACTION_RECOMMENDATION_PROMPT = """Based on this incident:
User {user_id} ({user_role}) performed {action} on `{table_name}` resulting in a threat score of {threat_score}/100.
Policies violated: {policies}

List 3 to 5 immediate, prioritized containment and remediation steps. Specify whether each action can be automatically executed or requires human authorization.
"""
