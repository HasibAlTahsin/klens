#!/usr/bin/env python3
"""
eval_threshold_tuning.py
Tests KLEnS at different Presidio score thresholds (0.3, 0.4, 0.5, 0.6, 0.7).
Does NOT need re-running the probe — directly calls analyze() with different thresholds.
Uses benchmark_v2.json ground truth.
"""
import json, os, sys

# We need to modify policy_engine's SCORE_THRESHOLD and re-analyze
# So we import the components directly
from presidio_analyzer import AnalyzerEngine

BENCH_FILE = 'benchmark_v2.json'
if not os.path.exists(BENCH_FILE):
    BENCH_FILE = 'benchmark.json'  # fallback to original

BENCH = json.load(open(BENCH_FILE))
analyzer = AnalyzerEngine()
ALLOWED = ['EMAIL_ADDRESS', 'PHONE_NUMBER', 'PERSON', 'CREDIT_CARD']

MIN_LEN = 4
def matches_any(det_val, truth_set):
    for t in truth_set:
        if len(t) >= MIN_LEN and t in det_val:
            return t
    return None

truth_values = set(r['truth_value'] for r in BENCH)

# For each threshold, analyze ALL benchmark prompts directly (no probe needed)
# This simulates what KLEnS would detect if the prompt content were echoed
thresholds = [0.3, 0.4, 0.5, 0.6, 0.7]

print(f'Testing {len(thresholds)} thresholds on {len(set(r["truth_value"] for r in BENCH))} unique PII values')
print(f'{"Threshold":>10} {"Precision":>10} {"Recall":>10} {"F1":>10} {"TP":>5} {"FP":>5} {"FN":>5}')
print('-' * 60)

results = {}
for thresh in thresholds:
    detected = set()
    # Analyze each unique prompt's PII content directly
    unique_prompts = set()
    for row in BENCH:
        p = row['prompt']
        if p in unique_prompts:
            continue
        unique_prompts.add(p)
        res = analyzer.analyze(text=p, language='en',
                               score_threshold=thresh, entities=ALLOWED)
        for r in res:
            detected.add(p[r.start:r.end])

    # Partial matching
    matched = set()
    tp = 0
    for d in detected:
        m = matches_any(d, truth_values)
        if m:
            tp += 1
            matched.add(m)
    fp = 0
    for d in detected:
        if not matches_any(d, truth_values):
            fp += 1
    fn = len(truth_values - matched)
    prec = tp / (tp + fp) if (tp + fp) else 0
    rec = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
    print(f'{thresh:>10.1f} {prec:>10.3f} {rec:>10.3f} {f1:>10.3f} {tp:>5} {fp:>5} {fn:>5}')
    results[str(thresh)] = {'precision': prec, 'recall': rec, 'f1': f1,
                            'TP': tp, 'FP': fp, 'FN': fn}

json.dump(results, open('threshold_tuning.json', 'w'), indent=2)
print(f'\nSaved to threshold_tuning.json')
print('\nDECISION: Pick the threshold that best balances precision and recall.')
print('Report ALL thresholds in the thesis (Table X) — do not cherry-pick.')
