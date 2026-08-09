#!/usr/bin/env python3
"""
eval_structured_vs_paraphrased.py
Runs benchmark_v2.json, measures KLEnS detection by category (structured vs paraphrased).
Also runs threshold tuning (0.3, 0.4, 0.5, 0.6, 0.7).
Requires: mock_pii_server.py on port 8080 + klens_probe.py attached to its PID.
"""
import json, time, requests, os, sys

BENCH_FILE = 'benchmark_v2.json'
LOG_FILE = 'klens_events.jsonl'
SERVER = 'http://127.0.0.1:8080/completion'

if not os.path.exists(BENCH_FILE):
    print(f'ERROR: {BENCH_FILE} not found. Run make_paraphrased_benchmark.py first.')
    sys.exit(1)

BENCH = json.load(open(BENCH_FILE))

# Clear previous log
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

print(f'Running {len(BENCH)} prompts (probe must be running)...')
for i, row in enumerate(BENCH):
    try:
        r = requests.post(SERVER, json={'prompt': row['prompt'], 'n_predict': 60}, timeout=30)
    except Exception as e:
        print(f'  [{i}] failed: {e}')
    if i % 50 == 0:
        print(f'  ...sent {i}/{len(BENCH)}')
    time.sleep(0.05)

print('All prompts sent. Waiting 5s for probe flush...')
time.sleep(5)

# ── Parse detected values ──
detected = set()
if os.path.exists(LOG_FILE):
    for line in open(LOG_FILE):
        try:
            ev = json.loads(line)
            for f in ev.get('findings', []):
                detected.add(f['value'])
        except:
            pass

# ── Partial matching ──
MIN_LEN = 4
def matches_any(det_val, truth_set):
    for t in truth_set:
        if len(t) >= MIN_LEN and t in det_val:
            return t
    return None

# ── Compute by category ──
for cat in ['structured', 'paraphrased', 'ALL']:
    if cat == 'ALL':
        truths = set(r['truth_value'] for r in BENCH)
    else:
        truths = set(r['truth_value'] for r in BENCH if r['category'] == cat)

    matched = set()
    tp = fp_count = 0
    for d in detected:
        m = matches_any(d, truths)
        if m:
            tp += 1
            matched.add(m)

    fn = len(truths - matched)
    p = tp / (tp + fn) if (tp + fn) else 0  # simplified for this context
    r = tp / (tp + fn) if (tp + fn) else 0
    # More accurate: precision needs FP from ALL detected not matching ANY truth
    all_truths = set(r2['truth_value'] for r2 in BENCH)
    real_fp = 0
    for d in detected:
        if not matches_any(d, all_truths):
            real_fp += 1

    if cat != 'ALL':
        print(f'\n=== {cat.upper()} PII ===')
        print(f'  Unique ground-truth: {len(truths)}')
        print(f'  Matched (TP): {tp}')
        print(f'  Missed (FN): {fn}')
        recall = tp / (tp + fn) if (tp + fn) else 0
        print(f'  Recall: {recall:.3f}')
    else:
        print(f'\n=== OVERALL ===')
        print(f'  Unique ground-truth: {len(truths)}')
        print(f'  Detected unique values: {len(detected)}')
        print(f'  TP (partial): {tp}  FP: {real_fp}  FN: {fn}')
        prec = tp / (tp + real_fp) if (tp + real_fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * prec * recall / (prec + recall) if (prec + recall) else 0
        print(f'  Precision: {prec:.3f}  Recall: {recall:.3f}  F1: {f1:.3f}')

# ── Per-jurisdiction ──
print('\n=== PER-JURISDICTION RECALL (partial match) ===')
for jur in ['EU', 'CN', 'IN']:
    truths_j = set(r['truth_value'] for r in BENCH if r['jurisdiction'] == jur)
    matched_j = set()
    for d in detected:
        m = matches_any(d, truths_j)
        if m:
            matched_j.add(m)
    tp_j = len(matched_j)
    fn_j = len(truths_j - matched_j)
    rec_j = tp_j / (tp_j + fn_j) if (tp_j + fn_j) else 0
    print(f'  {jur}: recall={rec_j:.3f} ({tp_j}/{tp_j+fn_j})')

# ── KEY FINDING: structured vs paraphrased delta ──
s_truths = set(r['truth_value'] for r in BENCH if r['category'] == 'structured')
p_truths = set(r['truth_value'] for r in BENCH if r['category'] == 'paraphrased')
s_matched = set()
p_matched = set()
for d in detected:
    ms = matches_any(d, s_truths)
    if ms: s_matched.add(ms)
    mp = matches_any(d, p_truths)
    if mp: p_matched.add(mp)

s_recall = len(s_matched) / len(s_truths) if s_truths else 0
p_recall = len(p_matched) / len(p_truths) if p_truths else 0

print(f'\n{"="*50}')
print(f'KEY FINDING (for legal argument):')
print(f'  Structured PII recall:   {s_recall:.3f} ({len(s_matched)}/{len(s_truths)})')
print(f'  Paraphrased PII recall:  {p_recall:.3f} ({len(p_matched)}/{len(p_truths)})')
print(f'  Delta:                   {s_recall - p_recall:+.3f}')
if s_recall > p_recall:
    print(f'  => Structured PII detected better than paraphrased.')
    print(f'  => Breach-detection for embedded/narrative PII is HARDER.')
elif abs(s_recall - p_recall) < 0.05:
    print(f'  => Similar recall — paraphrased PII detected comparably.')
else:
    print(f'  => Paraphrased detected better (unexpected — investigate).')
print(f'{"="*50}')

# Save results
results = {
    'structured_recall': s_recall,
    'paraphrased_recall': p_recall,
    'delta': s_recall - p_recall,
    'structured_matched': len(s_matched),
    'structured_total': len(s_truths),
    'paraphrased_matched': len(p_matched),
    'paraphrased_total': len(p_truths),
}
json.dump(results, open('structured_vs_paraphrased.json', 'w'), indent=2)
print('\nSaved to structured_vs_paraphrased.json')
