#!/usr/bin/env python3
"""
GraphGuard AI — Private Evaluation Runner
==========================================
Runs ONLY when manually executed.
NO production code is modified. NO frontend changes. NO LLM-as-judge.

Usage:
    python GraphGuard_Evaluation_Gold_Files/evaluate.py

Required env vars:
    EVAL_API_BASE_URL   — e.g. https://your-backend.onrender.com
    EVAL_EMAIL          — e.g. adi@gmail.com
    EVAL_PASSWORD       — account password

Outputs (all inside GraphGuard_Evaluation_Gold_Files/):
    evaluation_results.json
    question_results.csv
    evaluation_chart.png
    evidence_report.txt
"""

import os
import sys
import json
import time
import csv
import re
import requests
import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
QUESTIONS_FILE   = SCRIPT_DIR / "questions.json"
GOLD_ENTITIES    = SCRIPT_DIR / "gold_entities.json"
GOLD_RELS        = SCRIPT_DIR / "gold_relationships.json"
RESULTS_JSON     = SCRIPT_DIR / "evaluation_results.json"
RESULTS_CSV      = SCRIPT_DIR / "question_results.csv"
CHART_PNG        = SCRIPT_DIR / "evaluation_chart.png"
EVIDENCE_REPORT  = SCRIPT_DIR / "evidence_report.txt"


# ─────────────────────────────────────────────────────────────────────────────
# ENV VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def load_env():
    base_url  = os.environ.get("EVAL_API_BASE_URL", "").rstrip("/")
    email     = os.environ.get("EVAL_EMAIL", "")
    password  = os.environ.get("EVAL_PASSWORD", "")

    missing = []
    if not base_url:  missing.append("EVAL_API_BASE_URL")
    if not email:     missing.append("EVAL_EMAIL")
    if not password:  missing.append("EVAL_PASSWORD")

    if missing:
        print(f"\n  Missing required environment variables: {', '.join(missing)}")
        print("    Set them before running:\n")
        print("    export EVAL_API_BASE_URL=https://your-backend.onrender.com")
        print("    export EVAL_EMAIL=adi@gmail.com")
        print("    export EVAL_PASSWORD=your_password\n")
        sys.exit(1)

    return {"base_url": base_url, "email": email, "password": password}


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
def login(base_url, email, password):
    url = f"{base_url}/api/v1/auth/login"
    print(f"\n  Logging in as {email} ...")
    try:
        r = requests.post(url, json={"email": email, "password": password}, timeout=30)
        r.raise_for_status()
        token = r.json()["data"]["access_token"]
        print("      Login successful.")
        return token
    except requests.exceptions.HTTPError:
        print(f"\n  Login failed — HTTP {r.status_code}: {r.text}")
        sys.exit(1)
    except Exception as e:
        print(f"\n  Login error: {e}")
        sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH FETCH
# ─────────────────────────────────────────────────────────────────────────────
def fetch_graph(base_url, token):
    url = f"{base_url}/api/v1/graph"
    headers = {"Authorization": f"Bearer {token}"}
    print("  Fetching live knowledge graph ...")
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json().get("data", {})
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        print(f"      Graph fetched: {len(nodes)} nodes, {len(edges)} edges.")
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        print(f"\n  Failed to fetch graph: {e}")
        return {"nodes": [], "edges": []}


# ─────────────────────────────────────────────────────────────────────────────
# QUERY
# ─────────────────────────────────────────────────────────────────────────────
def ask_question(base_url, token, question, top_k=5):
    url = f"{base_url}/api/v1/query"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": question, "top_k": top_k, "filters": {}}

    start = time.time()
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=60)
        latency_ms = (time.time() - start) * 1000
        r.raise_for_status()
        data = r.json().get("data", {})
        data["_latency_ms"] = latency_ms
        data["_error"] = None
        return data
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return {
            "answer": "",
            "citations": [],
            "sources": [],
            "subgraph": {"nodes": [], "edges": []},
            "retrieval_stats": {},
            "_latency_ms": latency_ms,
            "_error": str(e),
        }


# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_entity_aliases(gold_entities):
    alias_map = {}
    for ent in gold_entities:
        canonical = ent["name"]
        norm_canonical = normalize(canonical)
        alias_map[norm_canonical] = norm_canonical
        for alias in ent.get("aliases", []):
            alias_map[normalize(alias)] = norm_canonical
    return alias_map


def get_actual_entity_names(graph_nodes, alias_map):
    resolved = set()
    for node in graph_nodes:
        raw = node.get("name", "") or node.get("label", "")
        norm = normalize(raw)
        if norm in alias_map:
            resolved.add(alias_map[norm])
        else:
            matched = False
            for alias_norm, canonical in alias_map.items():
                if alias_norm in norm or norm in alias_norm:
                    resolved.add(canonical)
                    matched = True
                    break
            if not matched:
                resolved.add(norm)
    return resolved


def get_gold_canonical_names(gold_entities, alias_map):
    return {alias_map[normalize(e["name"])] for e in gold_entities}


# ─────────────────────────────────────────────────────────────────────────────
# METRIC 1 — Retrieval Precision@5
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_retrieval_precision(question_results, questions):
    evaluable_qs = [q for q in questions if q["answerable"] and q.get("expected_sources")]
    if not evaluable_qs:
        return {"score": None, "reason": "No answerable questions with expected_sources defined."}

    precisions = []
    for q in evaluable_qs:
        qid = q["id"]
        result = next((r for r in question_results if r["id"] == qid), None)
        if not result or result.get("_error"):
            continue
        citations = result.get("citations", [])
        if not citations:
            precisions.append(0.0)
            continue
        expected_sources = [s.lower() for s in q["expected_sources"]]
        top_k = citations[:5]
        hits = 0
        for cit in top_k:
            doc_name = (cit.get("document_name") or "").lower()
            if any(exp in doc_name or doc_name in exp for exp in expected_sources):
                hits += 1
        precisions.append(hits / len(top_k))

    if not precisions:
        return {
            "score": None,
            "reason": "Citations were not returned by the API for any question. Retrieval Precision@5 is NOT measurable from current API responses.",
        }

    score = sum(precisions) / len(precisions)
    return {
        "score": round(score, 4),
        "reason": f"Computed over {len(precisions)} answerable questions with expected_sources.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# METRIC 2 — Entity Extraction F1
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_entity_extraction(graph_nodes, gold_entities):
    alias_map  = build_entity_aliases(gold_entities)
    gold_set   = get_gold_canonical_names(gold_entities, alias_map)
    actual_set = get_actual_entity_names(graph_nodes, alias_map)

    true_positives  = gold_set & actual_set
    false_positives = actual_set - gold_set
    false_negatives = gold_set - actual_set

    precision = len(true_positives) / len(actual_set) if actual_set else 0.0
    recall    = len(true_positives) / len(gold_set)   if gold_set   else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "precision": round(precision, 4),
        "recall":    round(recall,    4),
        "f1":        round(f1,        4),
        "true_positives":  sorted(true_positives),
        "false_positives": sorted(false_positives),
        "false_negatives": sorted(false_negatives),
        "gold_count":   len(gold_set),
        "actual_count": len(actual_set),
    }


# ─────────────────────────────────────────────────────────────────────────────
# METRIC 3 — Hallucination Containment
# ─────────────────────────────────────────────────────────────────────────────
REFUSAL_PHRASES = [
    "don't have", "do not have", "not found", "not available", "cannot find",
    "no information", "not mentioned", "not provided", "unable to find",
    "i don't know", "i do not know", "no data", "not covered", "not supported",
    "insufficient", "not present", "not referenced", "context does not",
    "not contain", "no record", "there is no", "is not mentioned",
    "is not provided", "outside the scope", "not specified", "no details",
    "couldn't find", "could not find", "not disclosed", "information is not",
    "not extracted", "not known", "this information", "no relevant",
    "beyond what", "not in the",
]

def evaluate_hallucination_containment(question_results, questions):
    unanswerable_qs = [q for q in questions if not q["answerable"]]
    if not unanswerable_qs:
        return {"score": None, "reason": "No NOT_FOUND questions in questions.json."}

    passed = 0
    failed_ids = []
    for q in unanswerable_qs:
        qid = q["id"]
        result = next((r for r in question_results if r["id"] == qid), None)
        if not result or result.get("_error"):
            failed_ids.append(qid)
            continue
        answer = result.get("answer", "").lower()
        if any(phrase in answer for phrase in REFUSAL_PHRASES):
            passed += 1
        else:
            failed_ids.append(qid)

    total = len(unanswerable_qs)
    return {
        "score":      round(passed / total, 4) if total else 0.0,
        "passed":     passed,
        "total":      total,
        "failed_ids": failed_ids,
        "reason":     f"{passed}/{total} NOT_FOUND questions correctly refused.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# METRIC 4 — Citation Traceability
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_citation_traceability(question_results, questions):
    answerable_qs = [q for q in questions if q["answerable"] and q.get("expected_keywords")]
    if not answerable_qs:
        return {"score": None, "reason": "No answerable questions with expected_keywords."}

    traceable = 0
    not_traceable_ids = []

    for q in answerable_qs:
        qid = q["id"]
        result = next((r for r in question_results if r["id"] == qid), None)
        if not result or result.get("_error"):
            not_traceable_ids.append(qid)
            continue

        citations = result.get("citations", [])
        if not citations:
            not_traceable_ids.append(qid)
            continue

        keywords = [kw.lower() for kw in q["expected_keywords"]]
        found = any(
            any(kw in (cit.get("snippet") or "").lower() for kw in keywords)
            for cit in citations
        )
        if found:
            traceable += 1
        else:
            not_traceable_ids.append(qid)

    total = len(answerable_qs)
    return {
        "score":             round(traceable / total, 4) if total else 0.0,
        "traceable":         traceable,
        "total":             total,
        "not_traceable_ids": not_traceable_ids,
        "reason":            f"{traceable}/{total} answerable questions had keyword-traceable citations.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# METRIC 5 — Answer Match Rate
# ─────────────────────────────────────────────────────────────────────────────
def evaluate_answer_match(question_results, questions):
    answerable_qs = [q for q in questions if q["answerable"] and q.get("expected_keywords")]
    if not answerable_qs:
        return {"score": None, "reason": "No answerable questions with expected_keywords."}

    matched = 0
    partial = 0
    missed_ids = []

    for q in answerable_qs:
        qid = q["id"]
        result = next((r for r in question_results if r["id"] == qid), None)
        if not result or result.get("_error"):
            missed_ids.append(qid)
            continue

        answer = result.get("answer", "").lower()
        keywords = [kw.lower() for kw in q["expected_keywords"]]
        hit_count = sum(1 for kw in keywords if kw in answer)

        if hit_count == len(keywords):
            matched += 1
        elif hit_count > 0:
            partial += 1
            missed_ids.append(qid)
        else:
            missed_ids.append(qid)

    total = len(answerable_qs)
    return {
        "score":           round(matched / total, 4) if total else 0.0,
        "full_matches":    matched,
        "partial_matches": partial,
        "total":           total,
        "missed_ids":      missed_ids,
        "reason":          f"{matched}/{total} questions had all expected keywords in answer.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# CHART
# ─────────────────────────────────────────────────────────────────────────────
def generate_chart(metrics):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError:
        print("\n  matplotlib not installed. Skipping chart. Run: pip install matplotlib")
        return

    COLOR_GOOD    = "#22c55e"
    COLOR_MEDIUM  = "#f59e0b"
    COLOR_BAD     = "#ef4444"
    COLOR_MISSING = "#64748b"

    def pick_color(v):
        if v is None: return COLOR_MISSING
        if v >= 0.75: return COLOR_GOOD
        if v >= 0.50: return COLOR_MEDIUM
        return COLOR_BAD

    metric_display = [
        ("Retrieval\nPrecision@5",    metrics.get("retrieval_precision_at_5",   {}).get("score")),
        ("Entity\nExtraction F1",     metrics.get("entity_extraction",          {}).get("f1")),
        ("Hallucination\nContainment", metrics.get("hallucination_containment",  {}).get("score")),
        ("Citation\nTraceability",    metrics.get("citation_traceability",      {}).get("score")),
        ("Answer\nMatch Rate",        metrics.get("answer_match_rate",          {}).get("score")),
    ]

    labels = [m[0] for m in metric_display]
    values = [m[1] if m[1] is not None else 0.0 for m in metric_display]
    colors = [pick_color(m[1]) for m in metric_display]

    fig, ax = plt.subplots(figsize=(12, 6), facecolor="#0f172a")
    ax.set_facecolor("#1e293b")

    x = np.arange(len(labels))
    bars = ax.bar(x, values, color=colors, width=0.52, zorder=3,
                  edgecolor="#334155", linewidth=1.2)

    for i, (label, val) in enumerate(metric_display):
        if val is None:
            ax.text(x[i], 0.04, "N/A", ha="center", va="bottom",
                    color="#94a3b8", fontsize=10, fontweight="bold")

    for bar, val in zip(bars, values):
        if val > 0.03:
            ax.text(bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 0.02,
                    f"{val:.0%}",
                    ha="center", va="bottom",
                    color="white", fontsize=11, fontweight="bold")

    for level, lbl in [(0.75, "Good (75%)"), (0.50, "Acceptable (50%)")]:
        ax.axhline(y=level, color="#475569", linestyle="--", linewidth=1, zorder=2, alpha=0.7)
        ax.text(len(labels) - 0.4, level + 0.012, lbl, color="#94a3b8", fontsize=8)

    ax.set_ylim(0, 1.15)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color="#cbd5e1", fontsize=11)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], color="#94a3b8")
    ax.tick_params(colors="#475569")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")

    ax.set_title("GraphGuard AI — Evaluation Metrics", color="white",
                 fontsize=14, fontweight="bold", pad=16)
    ax.set_ylabel("Score (0 – 1)", color="#94a3b8", fontsize=10)
    ax.grid(axis="y", color="#334155", linestyle="-", linewidth=0.5, zorder=1)

    legend_patches = [
        mpatches.Patch(color=COLOR_GOOD,    label=">= 75%  (Good)"),
        mpatches.Patch(color=COLOR_MEDIUM,  label="50-74% (Acceptable)"),
        mpatches.Patch(color=COLOR_BAD,     label="< 50%  (Needs work)"),
        mpatches.Patch(color=COLOR_MISSING, label="N/A"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", framealpha=0.2,
              labelcolor="white", fontsize=9)

    plt.tight_layout()
    plt.savefig(str(CHART_PNG), dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Chart saved: {CHART_PNG}")


# ─────────────────────────────────────────────────────────────────────────────
# CSV
# ─────────────────────────────────────────────────────────────────────────────
def save_csv(question_results, questions):
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id", "question", "answerable", "expected_answer", "expected_keywords",
            "actual_answer_snippet", "latency_ms", "citation_count",
            "sources_returned", "error",
        ])
        for q in questions:
            qid = q["id"]
            result = next((r for r in question_results if r["id"] == qid), {})
            answer = result.get("answer", "")
            answer_snippet = answer[:200].replace("\n", " ") if answer else ""
            sources = "|".join(result.get("sources", []))
            writer.writerow([
                qid, q["question"], q["answerable"], q["expected_answer"],
                "|".join(q.get("expected_keywords", [])),
                answer_snippet,
                f"{result.get('_latency_ms', 0):.1f}",
                len(result.get("citations", [])),
                sources,
                result.get("_error") or "",
            ])
    print(f"  CSV saved: {RESULTS_CSV}")


# ─────────────────────────────────────────────────────────────────────────────
# EVIDENCE REPORT
# ─────────────────────────────────────────────────────────────────────────────
def save_evidence_report(question_results, questions):
    with open(EVIDENCE_REPORT, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("GraphGuard AI -- Per-Question Evidence Report\n")
        f.write(f"Generated: {datetime.datetime.utcnow().isoformat()}Z\n")
        f.write("=" * 80 + "\n\n")

        for q in questions:
            qid = q["id"]
            result = next((r for r in question_results if r["id"] == qid), {})

            f.write(f"{'--'*35}\n")
            f.write(f"[{qid}] {q['question']}\n")
            f.write(f"  Answerable    : {q['answerable']}\n")
            f.write(f"  Expected      : {q['expected_answer']}\n")
            f.write(f"  Keywords      : {', '.join(q.get('expected_keywords', []))}\n")
            f.write(f"  Latency       : {result.get('_latency_ms', 0):.1f} ms\n")

            if result.get("_error"):
                f.write(f"  ERROR         : {result['_error']}\n")
            else:
                answer = result.get("answer", "")
                f.write(f"  Actual Answer :\n    {answer[:600]}\n")
                sources = result.get("sources", [])
                f.write(f"  Sources ({len(sources)}): {', '.join(sources) if sources else 'none'}\n")
                citations = result.get("citations", [])
                f.write(f"  Citations ({len(citations)}):\n")
                for i, cit in enumerate(citations[:5], 1):
                    doc = cit.get("document_name", "unknown")
                    snippet = (cit.get("snippet") or "")[:200].replace("\n", " ")
                    conf = cit.get("confidence_score", 0)
                    f.write(f"    [{i}] {doc} (conf={conf:.2f})\n        \"{snippet}\"\n")

            f.write("\n")

    print(f"  Evidence report saved: {EVIDENCE_REPORT}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 70)
    print("   GraphGuard AI -- Private Evaluation Runner")
    print("=" * 70)

    env           = load_env()
    questions     = json.loads(QUESTIONS_FILE.read_text())
    gold_entities = json.loads(GOLD_ENTITIES.read_text())
    gold_rels     = json.loads(GOLD_RELS.read_text())

    print(f"\n  Loaded {len(questions)} questions, "
          f"{len(gold_entities)} gold entities, "
          f"{len(gold_rels)} gold relationships.")

    token = login(env["base_url"], env["email"], env["password"])
    graph = fetch_graph(env["base_url"], token)

    print(f"\n  Sending {len(questions)} questions to /api/v1/query ...\n")
    question_results = []
    latencies = []

    for q in questions:
        print(f"  [{q['id']}] {q['question'][:72]}...")
        result = ask_question(env["base_url"], token, q["question"], top_k=5)
        result["id"] = q["id"]
        question_results.append(result)
        latencies.append(result["_latency_ms"])

        if result.get("_error"):
            print(f"         ERROR: {result['_error']}")
        else:
            ans_preview = result.get("answer", "")[:80].replace("\n", " ")
            print(f"         OK: {ans_preview}...")
        time.sleep(0.5)

    avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
    print(f"\n  Average query latency: {avg_latency_ms:.0f} ms")

    print("\n  Computing evaluation metrics ...\n")
    m_retrieval = evaluate_retrieval_precision(question_results, questions)
    m_entities  = evaluate_entity_extraction(graph["nodes"], gold_entities)
    m_halluc    = evaluate_hallucination_containment(question_results, questions)
    m_citation  = evaluate_citation_traceability(question_results, questions)
    m_answer    = evaluate_answer_match(question_results, questions)

    metrics = {
        "retrieval_precision_at_5":  m_retrieval,
        "entity_extraction":         m_entities,
        "hallucination_containment": m_halluc,
        "citation_traceability":     m_citation,
        "answer_match_rate":         m_answer,
    }

    results = {
        "evaluation_timestamp":  datetime.datetime.utcnow().isoformat() + "Z",
        "eval_email":            env["email"],
        "api_base_url":          env["base_url"],
        "questions_evaluated":   len(questions),
        "average_latency_ms":    round(avg_latency_ms, 1),
        "graph_node_count":      len(graph["nodes"]),
        "graph_edge_count":      len(graph["edges"]),
        "metrics":               metrics,
        "per_question_results":  [
            {
                "id":             r["id"],
                "answer":         r.get("answer", "")[:500],
                "latency_ms":     round(r["_latency_ms"], 1),
                "citation_count": len(r.get("citations", [])),
                "sources":        r.get("sources", []),
                "error":          r.get("_error"),
            }
            for r in question_results
        ],
    }

    def score_str(v):
        if v is None: return "N/A (not measurable)"
        return f"{v:.2%}"

    print("\n" + "=" * 70)
    print("   FINAL EVALUATION SCORES")
    print("=" * 70)
    print(f"  Retrieval Precision@5       : {score_str(m_retrieval.get('score'))}")
    if m_retrieval.get("score") is None:
        print(f"    -> {m_retrieval.get('reason', '')}")
    print(f"  Entity Extraction Precision : {score_str(m_entities.get('precision'))}")
    print(f"  Entity Extraction Recall    : {score_str(m_entities.get('recall'))}")
    print(f"  Entity Extraction F1        : {score_str(m_entities.get('f1'))}")
    print(f"    -> True Positives  : {m_entities.get('true_positives')}")
    print(f"    -> False Negatives : {m_entities.get('false_negatives')}")
    print(f"  Hallucination Containment   : {score_str(m_halluc.get('score'))}")
    print(f"    -> {m_halluc.get('reason', '')}")
    print(f"  Citation Traceability       : {score_str(m_citation.get('score'))}")
    print(f"    -> {m_citation.get('reason', '')}")
    print(f"  Answer Match Rate           : {score_str(m_answer.get('score'))}")
    print(f"    -> {m_answer.get('reason', '')}")
    print(f"\n  Average Query Latency       : {avg_latency_ms:.0f} ms")
    print(f"  Total Questions Run         : {len(questions)}")
    print("=" * 70)

    RESULTS_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n  Results saved: {RESULTS_JSON}")

    save_csv(question_results, questions)
    save_evidence_report(question_results, questions)
    generate_chart(metrics)

    print("\n  Evaluation complete!\n")


if __name__ == "__main__":
    main()
