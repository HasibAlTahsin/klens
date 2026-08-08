#!/usr/bin/env python3
import json, os, statistics

modes = ['baseline', 'metadata', 'full']
data = {}
for m in modes:
    path = f'overhead_{m}.json'
    if not os.path.exists(path): continue
    d = json.load(open(path))
    medians = [r['median_ms'] for r in d['runs']]
    data[m] = {'mean': statistics.mean(medians), 'std': statistics.stdev(medians) if len(medians)>1 else 0}

# JSON ফাইল সেভ করছি যাতে plot_results.py পড়তে পারে
json.dump(data, open('overhead_comparison.json','w'), indent=2)
print("Saved to overhead_comparison.json")
