#!/usr/bin/env python3
"""
Exact vs partial matching — boundary-tolerant precision/recall.
Reads existing klens_events.jsonl + benchmark.json (no re-run needed).
Reports BOTH numbers for honest thesis reporting.
"""
import json, os

# detected values পড়ো
det_values = set()
if os.path.exists('klens_events.jsonl'):
    for line in open('klens_events.jsonl'):
        try: ev = json.loads(line)
        except: continue
        for f in ev.get('findings', []):
            det_values.add(f['value'])

# ground-truth পড়ো
BENCH = json.load(open('benchmark.json'))
truth_values = set(row['truth_value'] for row in BENCH)

def pr(tp, fp, fn):
    p = tp/(tp+fp) if (tp+fp) else 0
    r = tp/(tp+fn) if (tp+fn) else 0
    f = 2*p*r/(p+r) if (p+r) else 0
    return p, r, f

# ── EXACT ──
TP_e = len(det_values & truth_values)
FP_e = len(det_values - truth_values)
FN_e = len(truth_values - det_values)
p_e, r_e, f_e = pr(TP_e, FP_e, FN_e)

# ── PARTIAL (boundary-tolerant) ──
# DECISION: len(truth) >= 4 guard যাতে ছোট string random match না করে।
# DECISION: শুধু 'truth in detected' (একদিকী, নিরাপদ)।
MIN_LEN = 4
def matches_any(detected, truths):
    for t in truths:
        if len(t) >= MIN_LEN and t in detected:
            return t
    return None

matched = set()
TP_p = FP_p = 0
for d in det_values:
    m = matches_any(d, truth_values)
    if m:
        TP_p += 1
        matched.add(m)
    else:
        FP_p += 1
FN_p = len(truth_values - matched)
p_p, r_p, f_p = pr(TP_p, FP_p, FN_p)

print("=" * 45)
print("EXACT match (strict):")
print(f"  Precision: {p_e:.3f}  Recall: {r_e:.3f}  F1: {f_e:.3f}")
print(f"  TP={TP_e} FP={FP_e} FN={FN_e}")
print("-" * 45)
print(f"PARTIAL match (boundary-tolerant, min_len={MIN_LEN}):")
print(f"  Precision: {p_p:.3f}  Recall: {r_p:.3f}  F1: {f_p:.3f}")
print(f"  TP={TP_p} FP={FP_p} FN={FN_p}")
print("=" * 45)

# false positive যেগুলো partial-এও FP থাকল (আসল ভুল):
print("\nসত্যিকারের FP (partial-এও মিলল না):")
for d in det_values:
    if not matches_any(d, truth_values):
        print(f"  {d!r}")

# দুটোই save করো (thesis-এর জন্য)
json.dump({
    'exact':   {'precision':p_e,'recall':r_e,'f1':f_e,'TP':TP_e,'FP':FP_e,'FN':FN_e},
    'partial': {'precision':p_p,'recall':r_p,'f1':f_p,'TP':TP_p,'FP':FP_p,'FN':FN_p},
}, open('accuracy_both.json','w'), indent=2)
print("\naccuracy_both.json-এ দুটো number save হলো")
