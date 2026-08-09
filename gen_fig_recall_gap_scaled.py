import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

labels = [
    "Phones / names / cards\nNER threshold & format",
    "EU IBAN\nentity whitelist (excluded)",
    "UnionPay 19-digit\nNER limitation (16-digit only)",
]
counts = [30, 10, 15]
jurs   = ["EU 20 · CN 2 · IN 8", "EU", "CN"]
colors = ["#7f8c8d", "#2c3e50", "#c0392b"]

fig, ax = plt.subplots(figsize=(10, 4))
y = range(len(counts))
bars = ax.barh(y, counts, color=colors, height=0.6)
for i, (b, c, j) in enumerate(zip(bars, counts, jurs)):
    ax.text(c + 0.6, i, f"{c}", va="center", fontsize=12, fontweight="bold")
    ax.text(33.5, i, j, va="center", fontsize=10, fontweight="bold", color=colors[i])
ax.set_yticks(list(y))
ax.set_yticklabels(labels, fontsize=10)
ax.set_xlim(0, 42)
ax.set_xlabel("Missed ground-truth PII values (total FN = 55)")
ax.set_title("Recall gap: cause analysis of 55 misses (scaled benchmark, n=180)")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout()
plt.savefig("fig_recall_gap_scaled.png", dpi=200, bbox_inches="tight")
print("wrote fig_recall_gap_scaled.png")
print("math check: 15+10+30 =", 15+10+30, "(must equal 55)")
