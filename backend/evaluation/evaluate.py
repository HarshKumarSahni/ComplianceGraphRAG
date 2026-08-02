#!/usr/bin/env python3
"""
GraphGuard AI — Private Automated Evaluation Module

Manual Execution:
    python evaluation/evaluate.py
  or:
    python backend/evaluation/evaluate.py

Environment Variables:
    EVAL_API_BASE_URL  (default: http://localhost:8000/api/v1)
    EVAL_EMAIL         (default: test@example.com)
    EVAL_PASSWORD      (default: password123)
"""

import os
import sys
import json
import time
import re
import csv
import urllib.request
import urllib.error
from typing import Dict, List, Any, Tuple, Optional

# Attempt matplotlib import for chart generation
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def normalize_text(s: str) -> str:
    """Normalize names and string labels for fuzzy matching."""
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r'[\-_"\',.]', ' ', s)
    return ' '.join(s.split())


class GraphGuardEvaluator:
    def __init__(self):
        self.base_url = os.environ.get("EVAL_API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
        self.email = os.environ.get("EVAL_EMAIL", "test@example.com")
        self.password = os.environ.get("EVAL_PASSWORD", "password123")

        # Resolve paths relative to this script's directory
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.questions_file = os.path.join(self.script_dir, "questions.json")
        self.gold_entities_file = os.path.join(self.script_dir, "gold_entities.json")
        self.gold_rels_file = os.path.join(self.script_dir, "gold_relationships.json")

        self.results_dir = os.path.join(self.script_dir, "results")
        os.makedirs(self.results_dir, exist_ok=True)

        self.token: Optional[str] = None
        self.questions: List[Dict[str, Any]] = []
        self.gold_entities: List[Dict[str, Any]] = []
        self.gold_relationships: List[Dict[str, Any]] = []

    def load_datasets(self):
        """Load benchmark evaluation files."""
        if not os.path.exists(self.questions_file):
            raise FileNotFoundError(f"Missing questions file: {self.questions_file}")
        if not os.path.exists(self.gold_entities_file):
            raise FileNotFoundError(f"Missing gold entities file: {self.gold_entities_file}")
        if not os.path.exists(self.gold_rels_file):
            raise FileNotFoundError(f"Missing gold relationships file: {self.gold_rels_file}")

        with open(self.questions_file, "r", encoding="utf-8") as f:
            self.questions = json.load(f)
        with open(self.gold_entities_file, "r", encoding="utf-8") as f:
            self.gold_entities = json.load(f).get("entities", [])
        with open(self.gold_rels_file, "r", encoding="utf-8") as f:
            self.gold_relationships = json.load(f).get("relationships", [])

    def _http_request(self, endpoint: str, method: str = "GET", payload: Optional[Dict] = None) -> Dict[str, Any]:
        """HTTP helper using standard library urllib."""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        data_bytes = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else str(e)
            raise RuntimeError(f"HTTP {e.code} Error for {url}: {err_body}")
        except Exception as e:
            raise RuntimeError(f"Request failed for {url}: {e}")

    def login(self) -> bool:
        """Authenticate with deployed backend and retrieve JWT access token."""
        print(f"[AUTH] Logging into {self.base_url} as {self.email}...")
        try:
            resp = self._http_request("/auth/login", method="POST", payload={"email": self.email, "password": self.password})
            data = resp.get("data", {})
            self.token = data.get("access_token") or data.get("token")
            if not self.token:
                raise ValueError(f"No access token returned in response: {resp}")
            print(f"[AUTH] Login successful! Token acquired.")
            return True
        except Exception as e:
            print(f"[ERROR] Auth failed: {e}")
            return False

    def evaluate_graph(self) -> Dict[str, Any]:
        """Fetch active Knowledge Graph and evaluate entity/relationship Precision, Recall, and F1."""
        print("[EVAL] Fetching Knowledge Graph for entity & relationship metric calculation...")
        try:
            resp = self._http_request("/graph", method="GET")
            graph_data = resp.get("data", {})
            actual_nodes = graph_data.get("nodes", [])
            actual_edges = graph_data.get("edges", [])
        except Exception as e:
            print(f"[WARNING] Graph endpoint call failed: {e}")
            actual_nodes, actual_edges = [], []

        # --- Entity Extraction Evaluation ---
        gold_norm_entities = {normalize_text(e["name"]) for e in self.gold_entities if "name" in e}
        actual_norm_entities = {normalize_text(n["name"]) for n in actual_nodes if n.get("name")}

        tp_entities = actual_norm_entities & gold_norm_entities
        ent_prec = len(tp_entities) / max(1, len(actual_norm_entities)) if actual_norm_entities else 0.0
        ent_rec = len(tp_entities) / max(1, len(gold_norm_entities)) if gold_norm_entities else 0.0
        ent_f1 = (2 * ent_prec * ent_rec) / (ent_prec + ent_rec) if (ent_prec + ent_rec) > 0 else 0.0

        # --- Relationship Evaluation ---
        gold_norm_rels = set()
        for r in self.gold_relationships:
            src = normalize_text(r.get("source", ""))
            tgt = normalize_text(r.get("target", ""))
            rel = normalize_text(r.get("relationship_type", r.get("type", "")))
            if src and tgt:
                gold_norm_rels.add((src, rel, tgt))

        actual_norm_rels = set()
        for e in actual_edges:
            src = normalize_text(e.get("source", e.get("source_entity", "")))
            tgt = normalize_text(e.get("target", e.get("target_entity", "")))
            rel = normalize_text(e.get("relationship_type", e.get("type", "")))
            if src and tgt:
                actual_norm_rels.add((src, rel, tgt))

        # True Positives: match (src, rel, tgt) OR match (src, tgt) semantic pair
        tp_rels = 0
        for src, rel, tgt in actual_norm_rels:
            if (src, rel, tgt) in gold_norm_rels:
                tp_rels += 1
            else:
                # Semantic match fallback: same source and target
                if any(g_src == src and g_tgt == tgt for (g_src, _, g_tgt) in gold_norm_rels):
                    tp_rels += 1

        rel_prec = tp_rels / max(1, len(actual_norm_rels)) if actual_norm_rels else 0.0
        rel_rec = tp_rels / max(1, len(gold_norm_rels)) if gold_norm_rels else 0.0
        rel_f1 = (2 * rel_prec * rel_rec) / (rel_prec + rel_rec) if (rel_prec + rel_rec) > 0 else 0.0

        return {
            "entity_count_extracted": len(actual_norm_entities),
            "entity_count_gold": len(gold_norm_entities),
            "entity_precision": round(ent_prec, 4),
            "entity_recall": round(ent_rec, 4),
            "entity_f1": round(ent_f1, 4),
            "relationship_count_extracted": len(actual_norm_rels),
            "relationship_count_gold": len(gold_norm_rels),
            "relationship_precision": round(rel_prec, 4),
            "relationship_recall": round(rel_rec, 4),
            "relationship_f1": round(rel_f1, 4),
        }

    def evaluate_questions(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Query deployed GraphRAG endpoint and evaluate Precision@5, Hallucination Containment, & Traceability."""
        question_results = []

        retrieval_precisions = []
        hallucination_containments = []
        citation_traceabilities = []
        latencies = []

        answerable_count = 0
        unanswerable_count = 0

        refusal_phrases = [
            "not found", "not provided", "not available", "cannot determine",
            "insufficient information", "not present", "does not contain",
            "no information", "unable to answer", "not mentioned",
            "don't have", "does not state", "does not specify", "no evidence"
        ]

        print(f"[EVAL] Running 15 benchmark queries against deployed /query API...")

        for idx, q in enumerate(self.questions, start=1):
            q_id = q["id"]
            question_text = q["question"]
            is_answerable = q.get("answerable", True)
            expected_kws = [k.lower() for k in q.get("expected_keywords", [])]
            expected_srcs = [s.lower() for s in q.get("expected_sources", [])]

            print(f"  [{idx}/15] {q_id}: {question_text[:50]}...")
            start_t = time.time()

            try:
                resp = self._http_request("/query", method="POST", payload={"question": question_text, "top_k": 5})
                latency_ms = round((time.time() - start_t) * 1000, 2)
                latencies.append(latency_ms)

                q_data = resp.get("data", {})
                actual_answer = q_data.get("answer", "")
                citations = q_data.get("citations", [])

            except Exception as e:
                latency_ms = round((time.time() - start_t) * 1000, 2)
                latencies.append(latency_ms)
                actual_answer = f"ERROR: Query call failed: {e}"
                citations = []

            # Evaluate per question type
            if is_answerable:
                answerable_count += 1

                # 1. Retrieval Precision@5
                # Check top 5 citations
                top_citations = citations[:5]
                relevant_citations = 0

                for c in top_citations:
                    snip = (c.get("snippet") or "").lower()
                    doc_name = (c.get("document_name") or "").lower()
                    is_rel = False
                    if any(kw in snip for kw in expected_kws):
                        is_rel = True
                    elif any(src in doc_name for src in expected_srcs) and len(snip) > 10:
                        is_rel = True
                    if is_rel:
                        relevant_citations += 1

                p_at_5 = relevant_citations / max(1, len(top_citations)) if top_citations else 0.0
                retrieval_precisions.append(p_at_5)

                # 2. Citation Traceability
                # Check if at least one citation matches expected source and contains evidence
                is_traceable = False
                for c in citations:
                    snip = (c.get("snippet") or "").lower()
                    doc_name = (c.get("document_name") or "").lower()
                    matches_src = any(src in doc_name for src in expected_srcs) or not expected_srcs
                    matches_kw = any(kw in snip for kw in expected_kws) or not expected_kws
                    if matches_src and matches_kw:
                        is_traceable = True
                        break
                citation_traceabilities.append(1.0 if is_traceable else 0.0)

                q_res = {
                    "id": q_id,
                    "question": question_text,
                    "answerable": True,
                    "expected_keywords": q.get("expected_keywords", []),
                    "expected_sources": q.get("expected_sources", []),
                    "actual_answer": actual_answer,
                    "citation_count": len(citations),
                    "retrieval_precision_at_5": round(p_at_5, 4),
                    "citation_traceable": is_traceable,
                    "latency_ms": latency_ms,
                }

            else:
                unanswerable_count += 1
                # 3. Hallucination Containment Rate (Deterministic refusal check)
                ans_lower = actual_answer.lower()
                contains_refusal = any(phrase in ans_lower for phrase in refusal_phrases)
                hallucination_containments.append(1.0 if contains_refusal else 0.0)

                q_res = {
                    "id": q_id,
                    "question": question_text,
                    "answerable": False,
                    "actual_answer": actual_answer,
                    "refusal_detected": contains_refusal,
                    "latency_ms": latency_ms,
                }

            question_results.append(q_res)

        avg_p_at_5 = sum(retrieval_precisions) / len(retrieval_precisions) if retrieval_precisions else 0.0
        avg_containment = sum(hallucination_containments) / len(hallucination_containments) if hallucination_containments else 0.0
        avg_traceability = sum(citation_traceabilities) / len(citation_traceabilities) if citation_traceabilities else 0.0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        qa_metrics = {
            "questions_tested": len(self.questions),
            "answerable_questions": answerable_count,
            "unanswerable_questions": unanswerable_count,
            "retrieval_precision_at_5": round(avg_p_at_5, 4),
            "hallucination_containment": round(avg_containment, 4),
            "citation_traceability": round(avg_traceability, 4),
            "average_latency_ms": round(avg_latency, 2),
        }

        return question_results, qa_metrics

    def generate_chart(self, summary: Dict[str, Any]):
        """Generate PPT-ready evaluation bar chart using matplotlib."""
        if not HAS_MATPLOTLIB:
            print("[WARNING] matplotlib is not installed. Skipping evaluation_chart.png generation.")
            return

        metrics_map = [
            ("Retrieval\nPrecision@5", summary.get("retrieval_precision_at_5")),
            ("Entity Extraction\nF1", summary.get("entity_f1")),
            ("Hallucination\nContainment", summary.get("hallucination_containment")),
            ("Citation\nTraceability", summary.get("citation_traceability")),
        ]

        labels = []
        values = []
        for label, val in metrics_map:
            if val is not None:
                labels.append(label)
                values.append(val * 100.0)

        if not labels:
            return

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ["#2563eb", "#059669", "#d97706", "#7c3aed"]

        bars = ax.bar(labels, values, color=colors[:len(labels)], width=0.55, edgecolor="#1e293b", linewidth=1.2)

        ax.set_ylim(0, 115)
        ax.set_ylabel("Score (%)", fontsize=12, fontweight="bold", labelpad=10)
        ax.set_title("GraphGuard Evaluation Results", fontsize=16, fontweight="bold", pad=20)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        # Style annotations above bars
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.1f}%",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=12,
                fontweight="bold",
                color="#0f172a",
            )

        plt.tight_layout()
        chart_path = os.path.join(self.results_dir, "evaluation_chart.png")
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f"[CHART] Saved evaluation bar chart to: {chart_path}")

    def save_summary_csv(self, summary: Dict[str, Any]):
        """Save metric summary to CSV."""
        csv_path = os.path.join(self.results_dir, "evaluation_summary.csv")
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Score_Percent", "Raw_Score"])
            for k, v in summary.items():
                if isinstance(v, (int, float)) and v <= 1.0 and not k.endswith("count") and not k.endswith("ms") and not k.endswith("tested"):
                    writer.writerow([k, f"{v * 100:.1f}%", v])
                else:
                    writer.writerow([k, "N/A", v])
        print(f"[CSV] Saved metrics summary to: {csv_path}")

    def run(self):
        """Execute full evaluation pipeline."""
        print("==================================================")
        print("         GRAPHGUARD PRIVATE EVALUATION            ")
        print("==================================================")

        self.load_datasets()

        if not self.login():
            sys.exit(1)

        graph_metrics = self.evaluate_graph()
        question_results, qa_metrics = self.evaluate_questions()

        # Combine summary metrics
        summary = {
            "questions_tested": qa_metrics["questions_tested"],
            "answerable_questions": qa_metrics["answerable_questions"],
            "unanswerable_questions": qa_metrics["unanswerable_questions"],
            "retrieval_precision_at_5": qa_metrics["retrieval_precision_at_5"],
            "entity_precision": graph_metrics["entity_precision"],
            "entity_recall": graph_metrics["entity_recall"],
            "entity_f1": graph_metrics["entity_f1"],
            "relationship_precision": graph_metrics["relationship_precision"],
            "relationship_recall": graph_metrics["relationship_recall"],
            "relationship_f1": graph_metrics["relationship_f1"],
            "hallucination_containment": qa_metrics["hallucination_containment"],
            "citation_traceability": qa_metrics["citation_traceability"],
            "average_latency_ms": qa_metrics["average_latency_ms"],
        }

        full_results = {
            "summary": summary,
            "questions": question_results,
        }

        json_path = os.path.join(self.results_dir, "evaluation_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(full_results, f, indent=2)
        print(f"[RESULTS] Saved full results JSON to: {json_path}")

        self.save_summary_csv(summary)
        self.generate_chart(summary)

        # Print clean terminal report
        print("\n" + "=" * 48)
        print("             GRAPHGUARD EVALUATION              ")
        print("=" * 48)
        print(f"Questions tested:              {summary['questions_tested']}")
        print(f"Answerable questions:          {summary['answerable_questions']}")
        print(f"Unanswerable questions:         {summary['unanswerable_questions']}\n")
        print(f"Retrieval Precision@5:        {summary['retrieval_precision_at_5']*100:.1f}%")
        print(f"Entity Extraction Precision:  {summary['entity_precision']*100:.1f}%")
        print(f"Entity Extraction Recall:     {summary['entity_recall']*100:.1f}%")
        print(f"Entity Extraction F1:         {summary['entity_f1']*100:.1f}%")
        print(f"Relationship F1:              {summary['relationship_f1']*100:.1f}%")
        print(f"Hallucination Containment:    {summary['hallucination_containment']*100:.1f}%")
        print(f"Citation Traceability:        {summary['citation_traceability']*100:.1f}%\n")
        print(f"Average Query Latency:        {summary['average_latency_ms']:.0f} ms")
        print("=" * 48 + "\n")


if __name__ == "__main__":
    evaluator = GraphGuardEvaluator()
    evaluator.run()
