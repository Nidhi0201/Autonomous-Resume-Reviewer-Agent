"""
Evaluation harness for the self-critique node.

Runs the critique over a labeled set of resume-bullet rewrites (faithful vs.
deliberately hallucinated) and reports how well it catches hallucinations:

  * recall            = hallucinated rewrites correctly flagged / all hallucinated
  * false-positive    = faithful rewrites wrongly flagged / all faithful
  * precision, accuracy, and a per-hallucination-type recall breakdown

The critique is queried at temperature 0 for reproducibility. Swap the prompt
with --prompt {baseline,improved} to compare variants; the numbers regenerate
whenever the prompt changes.

Usage (needs GROQ_API_KEY in backend/.env):
    cd backend && python -m eval.run_eval --prompt baseline
    cd backend && python -m eval.run_eval --prompt improved
"""
import argparse
import json
import time
from pathlib import Path

from app.llm import call_self_critique

EVAL_DIR = Path(__file__).parent
DATASET = EVAL_DIR / "dataset.json"
DATASET_REALISTIC = EVAL_DIR / "dataset_realistic.json"
DATASETS = {"synthetic": DATASET, "realistic": DATASET_REALISTIC}

# The original (weak) critique prompt, kept as a literal so the A/B stays
# reproducible even after the app adopts the improved prompt below.
BASELINE_CRITIQUE_PROMPT = (
    "You are a rigorous fact-checker. You validate resume improvements against "
    "original facts\nand flag any hallucinations or exaggerations."
)

# A stricter, more explicit critique prompt (the "improved" variant).
IMPROVED_CRITIQUE_PROMPT = """You are a strict resume fact-checker. Your only job is to decide whether an \
IMPROVED resume bullet is fully supported by the candidate's ORIGINAL resume.

Treat the resume as the ONLY source of truth. Set is_supported_by_resume = false if the improved \
bullet introduces ANYTHING not present in the resume, including:
- Any specific metric, number, percentage, or scale not stated in the resume \
(e.g. "by 45%", "3x", "500 daily users", "92% coverage", "30,000 records").
- Any tool, technology, framework, or platform not mentioned in the resume \
(e.g. Kubernetes, Kafka, Spark, Redis, Celery, RabbitMQ, D3.js, GraphQL).
- Any inflation of role, ownership, or scope beyond the resume \
(e.g. "led", "architected", "owned", "single-handedly", "managed a team", "production", \
"millions of users" when the resume describes a smaller or contributory role).

Rephrasing, adding job-relevant keywords that are already true, and clarifying existing facts \
are SUPPORTED (is_supported_by_resume = true). When in doubt about an added specific, treat it \
as unsupported.

List every unsupported addition in "issues". Respond in strict JSON with keys: \
self_critique, is_supported_by_resume (boolean), issues (array), evidence_snippets (array)."""

PROMPTS = {"baseline": BASELINE_CRITIQUE_PROMPT, "improved": IMPROVED_CRITIQUE_PROMPT}


def _is_flagged(result: dict) -> bool:
    """The node 'caught' a hallucination when it marks the rewrite unsupported."""
    val = result.get("is_supported_by_resume", True)
    if isinstance(val, str):
        supported = val.strip().lower() not in ("false", "no", "0")
    else:
        supported = bool(val)
    return not supported


def _critique_with_retry(ex, system_prompt, retries=4):
    jd = ex.get("job_description") or SHARED_JD
    for attempt in range(retries):
        result = call_self_critique(
            original_bullet=ex["original_bullet"],
            improved_bullet=ex["rewrite"],
            resume_text=ex["resume_text"],
            job_description=jd,
            system_prompt=system_prompt,
            temperature=0.0,
        )
        issues = result.get("issues", [])
        crit = str(result.get("self_critique", ""))
        # Don't retry non-transient failures (bad model id, auth, etc.).
        if "does not exist" in crit or "invalid_api_key" in crit or "404" in crit:
            raise RuntimeError(f"Non-transient Groq error: {crit[:160]}")
        # Daily token quota exhausted — retrying costs more quota and will
        # keep failing for hours. Surface it loudly instead of spinning.
        if "tokens per day" in crit or "TPD" in crit or "Upgrade to Dev Tier" in crit:
            raise RuntimeError(
                "Groq daily token quota exhausted — eval cannot continue. "
                "Wait for the daily reset or upgrade the Groq plan, then rerun."
            )
        if any("api_error" in str(i) or "not_json" in str(i) for i in issues):
            time.sleep(2 * (attempt + 1))  # backoff on rate-limit / transient
            continue
        return result
    return result


def evaluate(prompt_key: str, dataset_path: Path = DATASET, pace_s: float = 2.0) -> dict:
    data = json.loads(dataset_path.read_text())
    global SHARED_JD
    SHARED_JD = data["shared_job_description"]
    examples = data["examples"]
    system_prompt = PROMPTS[prompt_key]

    tp = fp = tn = fn = 0
    per_type = {}  # type -> [caught, total]
    mistakes = []  # (id, label, type, flagged) for FN + FP
    for ex in examples:
        flagged = _is_flagged(_critique_with_retry(ex, system_prompt))
        hallucinated = ex["label"] == "hallucinated"
        if hallucinated:
            per_type.setdefault(ex["type"], [0, 0])
            per_type[ex["type"]][1] += 1
            if flagged:
                tp += 1
                per_type[ex["type"]][0] += 1
            else:
                fn += 1
                mistakes.append({"id": ex["id"], "mistake": "false_negative",
                                 "type": ex["type"], "rewrite": ex["rewrite"]})
        else:
            if flagged:
                fp += 1
                mistakes.append({"id": ex["id"], "mistake": "false_positive",
                                 "type": None, "rewrite": ex["rewrite"]})
            else:
                tn += 1
        time.sleep(pace_s)  # stay under the free-tier ~30 req/min limit

    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fp_rate = fp / (fp + tn) if (fp + tn) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn)
    return {"prompt": prompt_key, "dataset": dataset_path.name,
            "n": len(examples), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "recall": recall, "false_positive_rate": fp_rate,
            "precision": precision, "accuracy": accuracy,
            "per_type": per_type, "mistakes": mistakes}


def _print_report(r: dict) -> None:
    print("\n" + "=" * 58)
    print(f"SELF-CRITIQUE EVAL  —  prompt: {r['prompt']}  dataset: {r['dataset']}  n: {r['n']}")
    print("=" * 58)
    print(f"  hallucination recall     {r['recall']*100:5.1f}%   ({r['tp']}/{r['tp']+r['fn']} caught)")
    print(f"  false-positive rate      {r['false_positive_rate']*100:5.1f}%   ({r['fp']}/{r['fp']+r['tn']} faithful flagged)")
    print(f"  precision                {r['precision']*100:5.1f}%")
    print(f"  accuracy                 {r['accuracy']*100:5.1f}%")
    print("  recall by hallucination type:")
    for t, (caught, total) in sorted(r["per_type"].items()):
        print(f"    {t:<22} {caught}/{total}")
    print("=" * 58)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", choices=list(PROMPTS), default="baseline")
    ap.add_argument("--compare", action="store_true", help="run both prompts and show before/after")
    ap.add_argument("--dataset", choices=list(DATASETS), default="synthetic",
                    help="which labeled set to evaluate on")
    ap.add_argument("--save", type=str, default=None,
                    help="write the raw results dict to this JSON path")
    args = ap.parse_args()

    dataset_path = DATASETS[args.dataset]

    if args.compare:
        results = {k: evaluate(k, dataset_path) for k in ("baseline", "improved")}
        for k in ("baseline", "improved"):
            _print_report(results[k])
        b, i = results["baseline"], results["improved"]
        print("\nBEFORE -> AFTER")
        print(f"  recall            {b['recall']*100:5.1f}%  ->  {i['recall']*100:5.1f}%")
        print(f"  false-positive    {b['false_positive_rate']*100:5.1f}%  ->  {i['false_positive_rate']*100:5.1f}%")
        payload = results
    else:
        res = evaluate(args.prompt, dataset_path)
        _print_report(res)
        payload = {args.prompt: res}

    if args.save:
        Path(args.save).write_text(json.dumps(payload, indent=2))
        print(f"\nwrote raw results to {args.save}")


if __name__ == "__main__":
    main()
