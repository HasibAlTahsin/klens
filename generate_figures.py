import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Fig 1: Exact vs Partial matching
fig, ax = plt.subplots(figsize=(8, 5))
metrics = ['Precision', 'Recall', 'F1-Score']
exact = [0.696, 0.842, 0.762]
partial = [1.000, 0.885, 0.939]
x = np.arange(len(metrics))
w = 0.32
b1 = ax.bar(x-w/2, exact, w, label='Exact match', color='#3498db')
b2 = ax.bar(x+w/2, partial, w, label='Partial match', color='#2ecc71')
for b in b1: ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02, f'{b.get_height():.3f}', ha='center', fontsize=11, fontweight='bold')
for b in b2: ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02, f'{b.get_height():.3f}', ha='center', fontsize=11, fontweight='bold')
ax.set_ylim(0, 1.15)
ax.set_ylabel('Score', fontsize=13)
ax.set_title('KLEnS Detection Accuracy: Exact vs Partial Matching', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=12)
ax.legend(fontsize=11)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('fig1_exact_vs_partial.png', dpi=200)
print('fig1_exact_vs_partial.png saved')
plt.close()

# Fig 2: Per-jurisdiction recall
fig, ax = plt.subplots(figsize=(7, 5))
jur = ['EU\n(GDPR+AI Act)', 'China\n(PIPL)', 'India\n(DPDP)']
rec = [0.750, 0.800, 1.000]
det = [6, 4, 6]
tot = [8, 5, 6]
bars = ax.bar(jur, rec, color=['#2c3e50','#c0392b','#f39c12'], width=0.55)
for b, d, t in zip(bars, det, tot):
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02, f'{b.get_height():.2f}\n({d}/{t})', ha='center', fontsize=11, fontweight='bold')
ax.set_ylim(0, 1.18)
ax.set_ylabel('Recall', fontsize=13)
ax.set_title('Detection Recall by Jurisdiction', fontsize=14, fontweight='bold')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('fig2_jurisdiction_recall.png', dpi=200)
print('fig2_jurisdiction_recall.png saved')
plt.close()

# Fig 3: Controlled vs Realistic (two panels)
fig, axes = plt.subplots(1, 2, figsize=(11, 5))
ax = axes[0]
ax.bar(['Controlled\n(Mock)', 'Realistic\n(TinyLlama)'], [253, 19], color=['#2ecc71','#e74c3c'], width=0.5)
for i, v in enumerate([253, 19]):
    ax.text(i, v+5, str(v), ha='center', fontsize=14, fontweight='bold')
ax.set_ylabel('Events logged (of 300 prompts)')
ax.set_title('Event Count')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax = axes[1]
m = ['Precision', 'Recall', 'F1']
c = [0.696, 0.842, 0.762]
r = [0.450, 0.474, 0.462]
x2 = np.arange(3)
ax.bar(x2-0.15, c, 0.3, label='Controlled', color='#2ecc71')
ax.bar(x2+0.15, r, 0.3, label='Realistic', color='#e74c3c')
for i in range(3):
    ax.text(i-0.15, c[i]+0.02, f'{c[i]:.2f}', ha='center', fontsize=10, fontweight='bold')
    ax.text(i+0.15, r[i]+0.02, f'{r[i]:.2f}', ha='center', fontsize=10, fontweight='bold')
ax.set_ylim(0, 1.1)
ax.set_ylabel('Score (exact)')
ax.set_title('Accuracy by Tier')
ax.set_xticks(x2)
ax.set_xticklabels(m)
ax.legend()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('fig3_controlled_vs_realistic.png', dpi=200)
print('fig3_controlled_vs_realistic.png saved')
plt.close()

# Fig 4: Precision improvement journey
fig, ax = plt.subplots(figsize=(8, 5))
stages = ['Initial\n(raw payload)', 'Content-fix\n(TinyLlama)', 'Controlled\n(exact)', 'Controlled\n(partial)']
vals = [0.14, 0.45, 0.70, 1.00]
bars = ax.bar(stages, vals, color=['#e74c3c','#f39c12','#3498db','#2ecc71'], width=0.6)
for b in bars:
    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.02, f'{b.get_height():.2f}', ha='center', fontsize=12, fontweight='bold')
ax.set_ylim(0, 1.18)
ax.set_ylabel('Precision')
ax.set_title('Precision Improvement Through Iterative Fixing', fontsize=14, fontweight='bold')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('fig4_precision_journey.png', dpi=200)
print('fig4_precision_journey.png saved')
plt.close()

# Fig 5: Recall gap (missed PII)
fig, ax = plt.subplots(figsize=(8, 4))
missed = ['UK phone (+44)', 'German IBAN', 'Chinese UnionPay\n(19-digit)']
causes = ['NER threshold', 'Entity whitelist\n(excluded)', 'NER limitation\n(16-digit only)']
y = np.arange(3)
ax.barh(y, [1,1,1], color=['#2c3e50','#2c3e50','#c0392b'], height=0.5)
ax.set_yticks(y)
ax.set_yticklabels(missed, fontsize=11)
for i, c_text in enumerate(causes):
    ax.text(0.05, i, c_text, ha='left', va='center', fontsize=9, color='white', fontweight='bold')
ax.text(1.3, 0, 'EU', fontsize=14, fontweight='bold', color='#2c3e50')
ax.text(1.3, 1, 'EU', fontsize=14, fontweight='bold', color='#2c3e50')
ax.text(1.3, 2, 'CN', fontsize=14, fontweight='bold', color='#c0392b')
ax.set_title('Recall Gap: 3 Missed PII Values', fontsize=14, fontweight='bold')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.set_xticks([])
plt.tight_layout()
plt.savefig('fig5_recall_gap.png', dpi=200)
print('fig5_recall_gap.png saved')
plt.close()

print('\n=== 5 figures generated ===')
