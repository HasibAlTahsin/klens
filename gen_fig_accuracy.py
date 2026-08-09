import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Load scaled-up results
r = json.load(open("accuracy_results.json"))
prec_s, rec_s, f1_s = r["precision"], r["recall"], r["f1"]

# Per-jurisdiction recall (scaled)
jur_recall = {"EU": 0.538, "CN": 0.717, "IN": 0.855}

# Original Tier 1 (n=300 prompts, 19 unique values)
orig_exact = {"P": 0.696, "R": 0.842, "F1": 0.762}
orig_partial = {"P": 1.000, "R": 0.885, "F1": 0.939}

fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

# Panel 1: Original Tier 1 — Exact vs Partial
ax = axes[0]
x = np.arange(3); w = 0.35
b1 = ax.bar(x - w/2, [orig_exact["P"], orig_exact["R"], orig_exact["F1"]], w,
            label="Exact", color="#2c7fb8", edgecolor="black", linewidth=0.5)
b2 = ax.bar(x + w/2, [orig_partial["P"], orig_partial["R"], orig_partial["F1"]], w,
            label="Partial", color="#7fcdbb", edgecolor="black", linewidth=0.5)
for bar in list(b1) + list(b2):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f"{bar.get_height():.3f}", ha="center", fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(["Precision", "Recall", "F1"])
ax.set_ylim(0, 1.15); ax.set_ylabel("Score")
ax.set_title("Original Tier 1 (n=19 unique)\nExact vs Partial Matching")
ax.legend(); ax.grid(axis="y", alpha=0.3)

# Panel 2: Scaled-up — Overall exact-match
ax = axes[1]
vals = [prec_s, rec_s, f1_s]
colors = ["#2c7fb8", "#fc8d59", "#7fcdbb"]
bars = ax.bar(["Precision", "Recall", "F1"], vals, color=colors, width=0.5,
              edgecolor="black", linewidth=0.5)
for bar, v in zip(bars, vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f"{v:.3f}", ha="center", fontsize=10, fontweight="bold")
ax.set_ylim(0, 1.15); ax.set_ylabel("Score")
ax.set_title(f"Scaled Benchmark (n=180 unique)\nExact Match")
ax.grid(axis="y", alpha=0.3)

# Panel 3: Scaled-up — Per-jurisdiction recall
ax = axes[2]
jur_labels = ["EU\n(65 values)", "CN\n(60 values)", "IN\n(55 values)"]
jur_vals = [jur_recall["EU"], jur_recall["CN"], jur_recall["IN"]]
colors_jur = ["#e31a1c", "#ff7f00", "#33a02c"]
bars = ax.bar(jur_labels, jur_vals, color=colors_jur, width=0.5,
              edgecolor="black", linewidth=0.5)
for bar, v in zip(bars, jur_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f"{v:.3f}", ha="center", fontsize=10, fontweight="bold")
ax.set_ylim(0, 1.15); ax.set_ylabel("Recall")
ax.set_title("Per-Jurisdiction Recall (Scaled)\nIBAN + UnionPay drag EU/CN")
ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
plt.savefig("fig_accuracy.png", dpi=200, bbox_inches="tight")
print("wrote fig_accuracy.png")
print(f"Panel 1: Original Tier 1 exact/partial")
print(f"Panel 2: Scaled P={prec_s:.3f} R={rec_s:.3f} F1={f1_s:.3f}")
print(f"Panel 3: EU={jur_recall['EU']:.3f} CN={jur_recall['CN']:.3f} IN={jur_recall['IN']:.3f}")
