#!/usr/bin/env python3
"""
GraphGuard AI — Private Evaluation Runner (Top@3 Edition)
==========================================================
Runs ONLY when manually executed. NO frontend changes. NO LLM-as-judge.

Config is read from evaluation_config.json in the same folder.
top_k is sourced from evaluation_config.json["retrieval_k"] = 3.

Usage:
    export EVAL_API_BASE_URL=https://your-backend.onrender.com
    export EVAL_EMAIL=adi@gmail.com
    export EVAL_PASSWORD=your_password
    python3 GraphGuard_Evaluation_Top3/evaluate.py

Outputs (all in GraphGuard_Evaluation_Top3/):
    evaluation_results.json
    question_results.csv
    evidence_report.txt
"""

import os
import sys
import json
import time
import urllib3

# Suppress SSL warnings — safe for a local private evaluation script
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import csv
import re
import requests
import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# PATHS — all resolved relative to this script's directory
# ---------------------------------------------------------------------------
SCRIPT_DIR    = Path(__file__).parent
CONFIG_FILE   = SCRIPT_DIR / "evaluation_config.json"
QUESTIONS_FILE = SCRIPT_DIR / "questions.json"
GOLD_ENTITIES  = SCRIPT_DIR / "gold_entities.json"
GOLD_RELS      = SCRIPT_DIR / "gold_relationships.json"
RESULTS_JSON   = SCRIPT_DIR / "evaluation_results.json"
RESULTS_CSV    = SCRIPT_DIR / "question_results.csv"
EVIDENCE_REPORT = SCRIPT_DIR / "evidence_report.txt"


# ---------------------------------------------------------------------------
# LOAD CONFIG
# ---------------------------------------------------------------------------
def load_config():
    if not CONFIG_FILE.exists():
        print(f"  ERROR: evaluation_config.json not found at {CONFIG_FILE}")
        sys.exit(1)
    cfg = json.loads(CONFIG_FILE.read_text())
    retrieval_k   = cfg.get("retrieval_k", 3)
    metric_name   = cfg.get("retrieval_metric_name", f"Retrieval Precision@{retrieval_k}")
    print(f"  Config loaded: retrieval_k={retrieval_k}, metric='{metric_name}'")
    return cfg, retrieval_k, metric_name


# ---------------------------------------------------------------------------
# ENV VALIDATION
# ---------------------------------------------------------------------------
def load_env():
    base_url = os.environ.get("EVAL_API_BASE_URL", "").rstrip("/")
    email    = os.environ.get("EVAL_EMAIL", "")
    password = os.environ.get("EVAL_PASSWORD", "")

    missing = []
    if not base_url:  missing.append("EVAL_API_BASE_URL")
    if not email:     missing.append("EVAL_EMAIL")
    if not password:  missing.append("EVAL_PASSWORD")

    if missing:
        print(f"\n  Missing environment variables: {', '.join(missing)}")
        print("\n  Set them first:")
        print("    export EVAL_API_BASE_URL=https://your-backend.onrender.com")
        print("    export EVAL_EMAIL=adi@gmail.com")
        print("    export EVAL_PASSWORD=your_password\n")
        sys.exit(1)

    return {"base_url": base_url, "email": email, "password": password}


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------
def login(base_url, email, password):
    url = f"{base_url}/api/v1/auth/login"
    print(f"\n  Logging in as {email} ...")
    try:
        r = requests.post(url, json={"email": email, "password": password}, timeout=30, verify=False)
        r.raise_for_status()
        token = r.json()["data"]["access_token"]
        print("      Login successful.")
        return token
    except requests.exceptions.HTTPError:
        print(f"  Login failed: HTTP {r.status_code}: {r.text}")
        sys.exit(1)
    except Exception as e:
        print(f"  Login error: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# GRAPH FETCH  /api/v1/graph
# ---------------------------------------------------------------------------
def fetch_graph(base_url, token):
    headers = {"Authorization": f"Bearer {token}"}
    print("  Fetching live knowledge graph ...")
    try:
        r = requests.get(f"{base_url}/api/v1/graph", headers=headers, timeout=30, verify=False)
        r.raise_for_status()
        data  = r.json().get("data", {})
        nodes = data.get("nodes", [])
        edges = data.get("edges", [])
        print(f"      {len(nodes)} nodes, {len(edges)} edges fetched.")
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        print(f"  Failed to fetch graph: {e}")
        return {"nodes": [], "edges": []}


# ---------------------------------------------------------------------------
# QUERY  /api/v1/query
# ---------------------------------------------------------------------------
def ask_question(base_url, token, question, top_k=3):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"question": question, "top_k": top_k, "filters": {}}
    start = time.time()
    try:
        r = requests.post(f"{base_url}/api/v1/query", json=payload,
                          headers=headers, timeout=60, verify=False)
        latency_ms = (time.time() - start) * 1000
        r.raise_for_status()
        data = r.json().get("data", {})
        data["_latency_ms"] = latency_ms
        data["_error"] = None
        return data
    except Exception as e:
        latency_ms = (time.time() - start) * 1000
        return {
            "answer": "", "citations": [], "sources": [],
            "subgraph": {}, "retrieval_stats": {},
            "_latency_ms": latency_ms, "_error": str(e),
        }


# ---------------------------------------------------------------------------
# NORMALIZATION HELPERS
# ---------------------------------------------------------------------------
def normalize(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_alias_map(gold_entities):
    """normalized alias -> normalized canonical name"""
    alias_map = {}
    for ent in gold_entities:
        canonical = normalize(ent["name"])
        alias_map[canonical] = canonical
        for alias in ent.get("aliases", []):
            alias_map[normalize(alias)] = canonical
    return alias_map


def resolve_actual_names(graph_nodes, alias_map):
    resolved = set()
    for node in graph_nodes:
        raw  = node.get("name", "") or node.get("label", "")
        norm = normalize(raw)
        if norm in alias_map:
            resolved.add(alias_map[norm])
        else:
            matched = False
            for alias, canonical in alias_map.items():
                if alias in norm or norm in alias:
                    resolved.add(canonical)
                    matched = True
                    break
            if not matched:
                resolved.add(norm)
    return resolved


def gold_canonical_set(gold_entities, alias_map):
    return {alias_map[normalize(e["name"])] for e in gold_entities}


# ---------------------------------------------------------------------------
# METRIC 1 — Retrieval Precision@K
# ---------------------------------------------------------------------------
def eval_retrieval_precision(question_results, questions, k):
    metric_name = f"Retrieval Precision@{k}"
    evaluable   = [q for q in questions if q["answerable"] and q.get("expected_sources")]
    if not evaluable:
        return {"score": None, "metric_name": metric_name,
                "reason": "No answerable questions with expected_sources."}

    precisions = []
    for q in evaluable:
        result = _find(question_results, q["id"])
        if not result or result.get("_error"):
            continue
        citations = result.get("citations", [])
        if not citations:
            precisions.append(0.0)
            continue
        expected = [s.lower() for s in q["expected_sources"]]
        top = citations[:k]
        hits = sum(
            1 for c in top
            if any(exp in (c.get("document_name") or "").lower() or
                   (c.get("document_name") or "").lower() in exp
                   for exp in expected)
        )
        precisions.append(hits / len(top))

    if not precisions:
        return {"score": None, "metric_name": metric_name,
                "reason": f"API returned no citations for any question. {metric_name} is not measurable from current API responses."}

    score = sum(precisions) / len(precisions)
    return {"score": round(score, 4), "metric_name": metric_name,
            "reason": f"Computed over {len(precisions)} answerable questions.",
            "per_question": precisions}


# ---------------------------------------------------------------------------
# METRIC 2 — Entity Extraction Precision / Recall / F1
# ---------------------------------------------------------------------------
def eval_entity_extraction(graph_nodes, gold_entities):
    alias_map  = build_alias_map(gold_entities)
    gold_set   = gold_canonical_set(gold_entities, alias_map)
    actual_set = resolve_actual_names(graph_nodes, alias_map)

    tp = gold_set & actual_set
    fp = actual_set - gold_set
    fn = gold_set - actual_set

    precision = len(tp) / len(actual_set) if actual_set else 0.0
    recall    = len(tp) / len(gold_set)   if gold_set   else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return {
        "precision":       round(precision, 4),
        "recall":          round(recall,    4),
        "f1":              round(f1,        4),
        "true_positives":  sorted(tp),
        "false_positives": sorted(fp),
        "false_negatives": sorted(fn),
        "gold_count":      len(gold_set),
        "actual_count":    len(actual_set),
    }


# ---------------------------------------------------------------------------
# METRIC 3 — Hallucination Containment
# ---------------------------------------------------------------------------
REFUSAL_PHRASES = [
    "don't have", "do not have", "not found", "not available", "cannot find",
    "no information", "not mentioned", "not provided", "unable to find",
    "i don't know", "i do not know", "no data", "not covered", "not supported",
    "insufficient", "not present", "not referenced", "context does not",
    "not contain", "no record", "there is no", "is not mentioned",
    "is not provided", "outside the scope", "not specified", "no details",
    "couldn't find", "could not find", "not disclosed", "information is not",
    "not extracted", "not known", "no relevant", "beyond what", "not in the",
    "this information",
]

def eval_hallucination(question_results, questions):
    unanswerable = [q for q in questions if not q["answerable"]]
    if not unanswerable:
        return {"score": None, "reason": "No NOT_FOUND questions in questions.json."}

    passed = 0
    failed_ids = []
    for q in unanswerable:
        result = _find(question_results, q["id"])
        if not result or result.get("_error"):
            failed_ids.append(q["id"])
            continue
        answer = result.get("answer", "").lower()
        if any(phrase in answer for phrase in REFUSAL_PHRASES):
            passed += 1
        else:
            failed_ids.append(q["id"])

    total = len(unanswerable)
    return {
        "score":      round(passed / total, 4) if total else 0.0,
        "passed":     passed,
        "total":      total,
        "failed_ids": failed_ids,
        "reason":     f"{passed}/{total} NOT_FOUND questions correctly refused.",
    }


# ---------------------------------------------------------------------------
# METRIC 4 — Citation Traceability
# ---------------------------------------------------------------------------
def eval_citation_traceability(question_results, questions):
    answerable = [q for q in questions if q["answerable"] and q.get("expected_keywords")]
    if not answerable:
        return {"score": None, "reason": "No answerable questions with expected_keywords."}

    traceable = 0
    not_traceable = []
    for q in answerable:
        result    = _find(question_results, q["id"])
        citations = (result or {}).get("citations", [])
        if not result or result.get("_error") or not citations:
            not_traceable.append(q["id"])
            continue
        keywords = [kw.lower() for kw in q["expected_keywords"]]
        found = any(
            any(kw in (c.get("snippet") or "").lower() for kw in keywords)
            for c in citations
        )
        if found:
            traceable += 1
        else:
            not_traceable.append(q["id"])

    total = len(answerable)
    return {
        "score":             round(traceable / total, 4) if total else 0.0,
        "traceable":         traceable,
        "total":             total,
        "not_traceable_ids": not_traceable,
        "reason":            f"{traceable}/{total} answerable questions had keyword-traceable citations.",
    }


# ---------------------------------------------------------------------------
# METRIC 5 — Answer Match Rate (keyword-based, no LLM)
# ---------------------------------------------------------------------------
def eval_answer_match(question_results, questions):
    answerable = [q for q in questions if q["answerable"] and q.get("expected_keywords")]
    if not answerable:
        return {"score": None, "reason": "No answerable questions with expected_keywords."}

    matched = 0
    partial = 0
    missed  = []
    for q in answerable:
        result   = _find(question_results, q["id"])
        answer   = (result or {}).get("answer", "").lower()
        keywords = [kw.lower() for kw in q["expected_keywords"]]
        hits     = sum(1 for kw in keywords if kw in answer)

        if hits == len(keywords):
            matched += 1
        elif hits > 0:
            partial += 1
            missed.append(q["id"])
        else:
            missed.append(q["id"])

    total = len(answerable)
    return {
        "score":            round(matched / total, 4) if total else 0.0,
        "full_matches":     matched,
        "partial_matches":  partial,
        "total":            total,
        "missed_ids":       missed,
        "reason":           f"{matched}/{total} questions had all expected keywords in answer.",
    }


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _find(results, qid):
    return next((r for r in results if r["id"] == qid), None)


def score_str(v):
    if v is None: return "N/A (not measurable)"
    return f"{v:.2%}"


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------
def save_csv(question_results, questions):
    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "question", "answerable", "expected_answer",
                    "expected_keywords", "actual_answer_snippet",
                    "latency_ms", "citation_count", "sources_returned", "error"])
        for q in questions:
            r = _find(question_results, q["id"]) or {}
            w.writerow([
                q["id"], q["question"], q["answerable"], q["expected_answer"],
                "|".join(q.get("expected_keywords", [])),
                (r.get("answer", "")[:200] or "").replace("\n", " "),
                f"{r.get('_latency_ms', 0):.1f}",
                len(r.get("citations", [])),
                "|".join(r.get("sources", [])),
                r.get("_error") or "",
            ])
    print(f"  CSV saved:      {RESULTS_CSV}")


# ---------------------------------------------------------------------------
# EVIDENCE REPORT
# ---------------------------------------------------------------------------
def save_evidence(question_results, questions):
    with open(EVIDENCE_REPORT, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("GraphGuard AI -- Per-Question Evidence Report (Top@3)\n")
        f.write(f"Generated: {datetime.datetime.utcnow().isoformat()}Z\n")
        f.write("=" * 80 + "\n\n")
        for q in questions:
            r = _find(question_results, q["id"]) or {}
            f.write("-" * 70 + "\n")
            f.write(f"[{q['id']}] {q['question']}\n")
            f.write(f"  Answerable : {q['answerable']}\n")
            f.write(f"  Expected   : {q['expected_answer']}\n")
            f.write(f"  Keywords   : {', '.join(q.get('expected_keywords', []))}\n")
            f.write(f"  Latency    : {r.get('_latency_ms', 0):.1f} ms\n")
            if r.get("_error"):
                f.write(f"  ERROR      : {r['_error']}\n")
            else:
                f.write(f"  Answer     :\n    {(r.get('answer',''))[:600]}\n")
                srcs = r.get("sources", [])
                f.write(f"  Sources    ({len(srcs)}): {', '.join(srcs) or 'none'}\n")
                cits = r.get("citations", [])
                f.write(f"  Citations  ({len(cits)}):\n")
                for i, c in enumerate(cits[:3], 1):
                    snippet = (c.get("snippet") or "")[:200].replace("\n", " ")
                    f.write(f"    [{i}] {c.get('document_name','?')} "
                            f"(conf={c.get('confidence_score',0):.2f})\n"
                            f"        \"{snippet}\"\n")
            f.write("\n")
    print(f"  Evidence saved: {EVIDENCE_REPORT}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("\n" + "=" * 70)
    print("   GraphGuard AI -- Evaluation Runner (Top@3)")
    print("=" * 70)

    cfg, retrieval_k, metric_name = load_config()
    env = load_env()

    questions     = json.loads(QUESTIONS_FILE.read_text())
    gold_entities = json.loads(GOLD_ENTITIES.read_text())
    gold_rels     = json.loads(GOLD_RELS.read_text())

    print(f"\n  Questions: {len(questions)}  |  "
          f"Gold entities: {len(gold_entities)}  |  "
          f"Gold relationships: {len(gold_rels)}")

    token = login(env["base_url"], env["email"], env["password"])
    graph = fetch_graph(env["base_url"], token)

    # ── Query every question ──────────────────────────────────────────────
    print(f"\n  Sending {len(questions)} questions (top_k={retrieval_k}) ...\n")
    question_results = []
    latencies = []

    for q in questions:
        print(f"  [{q['id']}] {q['question'][:72]}...")
        result = ask_question(env["base_url"], token, q["question"], top_k=retrieval_k)
        result["id"] = q["id"]
        question_results.append(result)
        latencies.append(result["_latency_ms"])

        if result.get("_error"):
            print(f"         ERROR: {result['_error']}")
        else:
            preview = result.get("answer", "")[:80].replace("\n", " ")
            print(f"         OK ({result['_latency_ms']:.0f}ms): {preview}...")
        time.sleep(0.4)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    print(f"\n  Average latency: {avg_latency:.0f} ms")

    # ── Compute metrics ───────────────────────────────────────────────────
    print("\n  Computing metrics ...\n")
    m_retrieval = eval_retrieval_precision(question_results, questions, retrieval_k)
    m_entities  = eval_entity_extraction(graph["nodes"], gold_entities)
    m_halluc    = eval_hallucination(question_results, questions)
    m_citation  = eval_citation_traceability(question_results, questions)
    m_answer    = eval_answer_match(question_results, questions)

    metrics = {
        f"retrieval_precision_at_{retrieval_k}": m_retrieval,
        "entity_extraction":                     m_entities,
        "hallucination_containment":             m_halluc,
        "citation_traceability":                 m_citation,
        "answer_match_rate":                     m_answer,
    }

    # ── Print scores ──────────────────────────────────────────────────────
    print("=" * 70)
    print("   FINAL EVALUATION SCORES")
    print("=" * 70)
    print(f"  {metric_name:<28}: {score_str(m_retrieval.get('score'))}")
    if m_retrieval.get("score") is None:
        print(f"    -> {m_retrieval.get('reason','')}")
    print(f"  Entity Extraction Precision : {score_str(m_entities.get('precision'))}")
    print(f"  Entity Extraction Recall    : {score_str(m_entities.get('recall'))}")
    print(f"  Entity Extraction F1        : {score_str(m_entities.get('f1'))}")
    print(f"    -> TP: {m_entities.get('true_positives')}")
    print(f"    -> FN: {m_entities.get('false_negatives')}")
    print(f"  Hallucination Containment   : {score_str(m_halluc.get('score'))}")
    print(f"    -> {m_halluc.get('reason','')}")
    print(f"  Citation Traceability       : {score_str(m_citation.get('score'))}")
    print(f"    -> {m_citation.get('reason','')}")
    print(f"  Answer Match Rate           : {score_str(m_answer.get('score'))}")
    print(f"    -> {m_answer.get('reason','')}")
    print(f"\n  Average Latency             : {avg_latency:.0f} ms")
    print(f"  Questions Evaluated         : {len(questions)}")
    print("=" * 70)

    # ── Save outputs ──────────────────────────────────────────────────────
    output = {
        "evaluation_timestamp":  datetime.datetime.utcnow().isoformat() + "Z",
        "eval_email":            env["email"],
        "api_base_url":          env["base_url"],
        "retrieval_k":           retrieval_k,
        "metric_name":           metric_name,
        "questions_evaluated":   len(questions),
        "average_latency_ms":    round(avg_latency, 1),
        "graph_node_count":      len(graph["nodes"]),
        "graph_edge_count":      len(graph["edges"]),
        "metrics":               metrics,
        "per_question_results":  [
            {
                "id":             r["id"],
                "answer":         (r.get("answer") or "")[:500],
                "latency_ms":     round(r["_latency_ms"], 1),
                "citation_count": len(r.get("citations", [])),
                "sources":        r.get("sources", []),
                "error":          r.get("_error"),
            }
            for r in question_results
        ],
    }

    RESULTS_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n  Results saved:  {RESULTS_JSON}")

    save_csv(question_results, questions)
    save_evidence(question_results, questions)

    print("\n  Evaluation complete!\n")


if __name__ == "__main__":
    main()
