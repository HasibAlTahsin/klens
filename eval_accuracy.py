#!/usr/bin/env python3
"""Evaluate KLEnS detection accuracy against benchmark."""
import json, time, requests, os

BENCH = json.load(open('benchmark.json'))
LOG = 'klens_events.jsonl'
SERVER = 'http://127.0.0.1:8080/completion'

# Clear previous log
if os.path.exists(LOG): os.remove(LOG)

print(f'Running {len(BENCH)} prompts (probe must be running in another terminal)...')
for i, row in enumerate(BENCH):
    try:
        r = requests.post(SERVER, json={'prompt': row['prompt'], 'n_predict': 60}, timeout=30)
    except Exception as e:
        print(f' [{i}] request failed: {e}')
    if i % 50 == 0:
        print(f' ...sent {i}/{len(BENCH)}')
    time.sleep(0.1) # avoid overwhelming the server

print('All prompts sent. Waiting 5s for probe to flush...')
time.sleep(5)

# ---- PARSE KLENS LOG ----
detected = []
if os.path.exists(LOG):
    with open(LOG) as f:
        for line in f:
            detected.append(json.loads(line.strip()))

# Flatten detected entity values
det_values = set()
det_entities = []
for ev in detected:
    for finding in ev.get('findings', []):
        det_values.add(finding['value'])
        det_entities.append((finding['entity'], finding['value']))

# ---- COMPUTE PRECISION / RECALL ----
truth_values = set(row['truth_value'] for row in BENCH)

TP = len(det_values & truth_values)
FP = len(det_values - truth_values)
FN = len(truth_values - det_values)

precision = TP / (TP + FP) if (TP + FP) > 0 else 0
recall = TP / (TP + FN) if (TP + FN) > 0 else 0
f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f'\n=== KLEnS Detection Accuracy ===')
print(f'Benchmark prompts: {len(BENCH)}')
print(f'Events logged: {len(detected)}')
print(f'Unique PII found: {len(det_values)}')
print(f'TP={TP} FP={FP} FN={FN}')
print(f'Precision: {precision:.3f}')
print(f'Recall: {recall:.3f}')
print(f'F1: {f1:.3f}')

# Per-jurisdiction breakdown
for jur in ['EU','CN','IN']:
    jur_truth = set(r['truth_value'] for r in BENCH if r['jurisdiction']==jur)
    jur_tp = len(det_values & jur_truth)
    jur_fn = len(jur_truth - det_values)
    jur_recall = jur_tp/(jur_tp+jur_fn) if (jur_tp+jur_fn)>0 else 0
    print(f' {jur}: recall={jur_recall:.3f} ({jur_tp}/{jur_tp+jur_fn})')

# Save results
results = {'precision':precision,'recall':recall,'f1':f1,'TP':TP,'FP':FP,'FN':FN}
json.dump(results, open('accuracy_results.json','w'), indent=2)
print('\nSaved to accuracy_results.json')
