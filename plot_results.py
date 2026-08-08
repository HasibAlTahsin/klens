#!/usr/bin/env python3
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Overhead Plot
d = json.load(open('overhead_comparison.json'))
modes = [m for m in ['baseline','metadata','full'] if m in d]
means = [d[m]['mean'] for m in modes]
errs = [d[m]['std'] for m in modes]
labels = {'baseline':'No probe','metadata':'Metadata-only\n(Falco-like)','full':'Full KLEnS'}

plt.figure(figsize=(6,4))
bars = plt.bar([labels[m] for m in modes], means, yerr=errs, capsize=6, color=['#95a5a6','#3498db','#e74c3c'])
plt.ylabel('Median latency (ms)')
plt.title('KLEnS Overhead by Mode')
for b,m in zip(bars,means):
    plt.text(b.get_x()+b.get_width()/2, m, f'{m:.1f}', ha='center', va='bottom')
plt.tight_layout()
plt.savefig('fig_overhead.png', dpi=150)
print('wrote fig_overhead.png')

# Accuracy Plot
if os.path.exists('accuracy_results.json'):
    a = json.load(open('accuracy_results.json'))
    metrics = ['precision','recall','f1']
    vals = [a[m] for m in metrics]
    plt.figure(figsize=(5,4))
    plt.bar(metrics, vals, color='#2ecc71')
    plt.ylim(0,1)
    plt.ylabel('Score')
    plt.title('KLEnS Detection Accuracy')
    for i,v in enumerate(vals):
        plt.text(i, v, f'{v:.2f}', ha='center', va='bottom')
    plt.tight_layout()
    plt.savefig('fig_accuracy.png', dpi=150)
    print('wrote fig_accuracy.png')
