# Self-critique evaluation

Measures how well the self-critique node catches hallucinated resume-bullet
rewrites.

## Datasets

| name | file | n | notes |
|---|---|---|---|
| `synthetic` | `dataset.json` | 30 | Original short-context examples. 15 faithful / 15 hallucinated across 3 types (`invented_metric`, `fabricated_tool`, `inflated_scope`). |
| `realistic` | `dataset_realistic.json` | 70 | Longer, more realistic resume contexts (1–3 sentences). 35 faithful / 35 hallucinated across 6 types — adds `false_outcome`, `timeline_fabrication`, `team_size_inflation`. |

Realistic examples use intern/new-grad resume contexts (small teams, class
projects, hackathons, modest scale) and include subtle cases: outcome claims
not stated in the resume ("prevented three near-miss outages"), timeline
inflation ("spent a year contributing" when the resume shows a weekend),
team-size inflation ("led eight engineers" when the resume shows a pair).

## Running

```bash
# .env must have GROQ_API_KEY
cd backend
python -m eval.run_eval                                 # synthetic, baseline prompt
python -m eval.run_eval --compare                       # synthetic, both prompts, before/after
python -m eval.run_eval --dataset realistic --compare   # realistic (recommended)
python -m eval.run_eval --dataset realistic --prompt improved \
  --save eval/results/realistic_improved.json           # save raw results JSON
```

The runner paces at 2s/call to stay under Groq's rate limit. 70 examples × 2
prompts × 2s ≈ ~5 min minimum (plus LLM latency). If you hit the daily token
quota, the harness raises a clear error instead of spinning.

Metrics reported:

- **recall** — fraction of hallucinated rewrites correctly flagged
- **false-positive rate** — fraction of faithful rewrites wrongly flagged
- **precision**, **accuracy**
- **per-type recall** — breakdown by hallucination class

## Files

- `dataset.json` — the original 30 synthetic examples
- `dataset_realistic.json` — 70 realistic examples (this expansion)
- `run_eval.py` — the harness
- `results/` — raw JSON results (written when `--save` is passed)

## Interpreting results

Expect lower numbers on `realistic` than on `synthetic`: longer contexts give
the model more surface area to confuse "stated" with "implied", and the three
new hallucination types (`false_outcome`, `timeline_fabrication`,
`team_size_inflation`) stress patterns the baseline prompt wasn't tuned on.
The gap between `baseline` and `improved` on `realistic` is the better
signal for whether the improved prompt actually generalizes.
