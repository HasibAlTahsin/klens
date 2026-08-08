#!/usr/bin/env python3
"""
eval_overhead.py — 3-mode overhead benchmark for KLEnS.
MUST run on bare-metal Ubuntu, not a VM.

Usage:
MODE 1 (baseline): python3 eval_overhead.py baseline
MODE 2 (metadata-only): python3 eval_overhead.py metadata
(run probe with PII_ANALYSIS=0)
MODE 3 (full KLEnS): python3 eval_overhead.py full
(run probe normally)
"""
import sys, time, json, statistics, requests

MODE = sys.argv[1] if len(sys.argv) > 1 else 'baseline'
SERVER = 'http://127.0.0.1:8080/completion'
N_WARMUP = 20
N_REQUESTS = 200
N_RUNS = 3 # repeat 3 times for mean + stddev

PROMPT = 'User: alice@corp.com, +44 7700 900123. Confirm receipt.'

def single_run():
    latencies = []
    for i in range(N_WARMUP + N_REQUESTS):
        t0 = time.perf_counter()
        try:
            r = requests.post(SERVER, json={'prompt': PROMPT, 'n_predict': 20}, timeout=30)
        except Exception as e:
            print(f' req {i} failed: {e}')
            continue
        t1 = time.perf_counter()
        if i >= N_WARMUP: # skip warmup
            latencies.append((t1 - t0) * 1000) # ms
    return latencies

all_results = []
for run in range(N_RUNS):
    print(f'[{MODE}] Run {run+1}/{N_RUNS}...')
    lats = single_run()
    med = statistics.median(lats)
    p99 = sorted(lats)[int(len(lats)*0.99)] if lats else 0
    rps = 1000.0 / med if med > 0 else 0
    all_results.append({
        'run': run+1,
        'n': len(lats),
        'median_ms': round(med, 2),
        'p99_ms': round(p99, 2),
        'mean_ms': round(statistics.mean(lats), 2),
        'stddev_ms': round(statistics.stdev(lats), 2) if len(lats) > 1 else 0,
        'req_per_sec': round(rps, 2),
    })
    print(f' median={med:.1f}ms p99={p99:.1f}ms rps={rps:.1f}')

# Save
outfile = f'overhead_{MODE}.json'
json.dump({'mode': MODE, 'runs': all_results}, open(outfile, 'w'), indent=2)
print(f'\nSaved to {outfile}')

# Summary
medians = [r['median_ms'] for r in all_results]
print(f'\n=== {MODE.upper()} SUMMARY ===')
print(f'Median latency: {statistics.mean(medians):.1f} ± {statistics.stdev(medians):.1f} ms')
