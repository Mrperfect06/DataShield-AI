"""
DataShield AI — Security Policy & Forensics RAG Knowledge Base
===============================================================
Indexes security guidelines, regulatory frameworks (GDPR, HIPAA, SOC2),
and historical breach incidents for context-grounded threat explanation.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import DATA_DIR, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


class SecurityKnowledgeBase:
    """
    RAG repository storing security policies and historical incident narratives.
    Uses TF-IDF semantic matching as resilient local retrieval, with optional ChromaDB expansion.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or CHROMA_PERSIST_DIR
        self.policies: List[Dict[str, Any]] = []
        self.incidents: List[Dict[str, Any]] = []
        self.corpus_docs: List[str] = []
        self.metadata_index: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        
        # Load policies & incidents on initialization
        self.load_data()

    def load_data(
        self,
        policies_path: Optional[Path] = None,
        incidents_path: Optional[Path] = None,
    ):
        p_path = policies_path or (DATA_DIR / "policies" / "security_policies.json")
        i_path = incidents_path or (DATA_DIR / "policies" / "incident_history.json")

        if p_path.exists():
            try:
                with open(p_path, "r", encoding="utf-8") as f:
                    self.policies = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load policies from {p_path}: {e}")

        if i_path.exists():
            try:
                with open(i_path, "r", encoding="utf-8") as f:
                    self.incidents = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load incidents from {i_path}: {e}")

        self._build_index()

    def _build_index(self):
        self.corpus_docs = []
        self.metadata_index = []

        # Index Policies
        for p in self.policies:
            text = f"Policy {p.get('id', '')}: {p.get('title', '')}. Category: {p.get('category', '')}. " \
                   f"{p.get('description', '')} Frameworks: {', '.join(p.get('compliance_frameworks', []))}. " \
                   f"Automated Action: {p.get('automated_response', '')}"
            self.corpus_docs.append(text)
            self.metadata_index.append({"type": "policy", "data": p})

        # Index Incidents
        for inc in self.incidents:
            text = f"Incident {inc.get('incident_id', '')}: {inc.get('summary', '')} Threat: {inc.get('threat_type', '')}. " \
                   f"Indicators: {', '.join(inc.get('indicators', []))}. Resolution: {inc.get('resolution', '')}"
            self.corpus_docs.append(text)
            self.metadata_index.append({"type": "incident", "data": inc})

        if _SKLEARN_AVAILABLE and self.corpus_docs:
            self.vectorizer = TfidfVectorizer(stop_words="english")
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_docs)

    def query(self, query_text: str, n_results: int = 4) -> List[Dict[str, Any]]:
        """
        Retrieves top n relevant policies or historical records based on query.
        """
        if not self.corpus_docs:
            return []

        if self.vectorizer and self.tfidf_matrix is not None:
            query_vec = self.vectorizer.transform([query_text])
            scores = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            top_indices = scores.argsort()[::-1][:n_results]
            
            results = []
            for idx in top_indices:
                if scores[idx] > 0.01:
                    results.append({
                        "score": float(scores[idx]),
                        "type": self.metadata_index[idx]["type"],
                        "content": self.corpus_docs[idx],
                        "details": self.metadata_index[idx]["data"],
                    })
            return results

        # Simple string keyword match fallback
        query_lower = query_text.lower()
        matched = []
        for idx, doc in enumerate(self.corpus_docs):
            if any(term in doc.lower() for term in query_lower.split() if len(term) > 3):
                matched.append({
                    "score": 0.5,
                    "type": self.metadata_index[idx]["type"],
                    "content": doc,
                    "details": self.metadata_index[idx]["data"],
                })
            if len(matched) >= n_results:
                break
        return matched

    def get_relevant_policies(self, keywords: List[str], severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Finds security policies matching specific keywords or severity level."""
        if not keywords:
            # Baseline normal access policy
            for p in self.policies:
                if p.get("id") == "POL-000":
                    return [p]
            return [self.policies[0]] if self.policies else []

        matches = []
        for p in self.policies:
            text = (p.get("title", "") + " " + p.get("description", "") + " " + p.get("category", "")).lower()
            if any(k.lower() in text for k in keywords):
                if severity is None or p.get("severity", "").lower() == severity.lower():
                    matches.append(p)
        return matches[:4] if matches else [self.policies[0]] if self.policies else []

    def get_similar_incidents(self, indicators: List[str]) -> List[Dict[str, Any]]:
        """Matches previous breach patterns to current anomaly indicators."""
        if not indicators:
            return []

        matches = []
        for inc in self.incidents:
            inc_inds = [i.lower() for i in inc.get("indicators", [])]
            for ind in indicators:
                if any(ind.lower() in ii or ii in ind.lower() for ii in inc_inds):
                    matches.append(inc)
                    break
        return matches[:3]


if __name__ == "__main__":
    kb = SecurityKnowledgeBase()
    print(f"Loaded {len(kb.policies)} policies and {len(kb.incidents)} historical incidents.")
    res = kb.query("bulk download after hours PII exfiltration")
    print("\nTop Query Results:")
    for r in res:
        print(f"[{r['type'].upper()} - score {r['score']:.3f}] {r['content'][:120]}...")
