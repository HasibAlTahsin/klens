import json, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from presidio_analyzer import AnalyzerEngine
ENT=["EMAIL_ADDRESS","PHONE_NUMBER","PERSON","CREDIT_CARD"]; THR=0.4
an=AnalyzerEngine()
def detect_entities(t):
    if not t: return []
    return [t[r.start:r.end] for r in an.analyze(text=t,language="en",entities=ENT,score_threshold=THR)]
def full_content(raw):
    try: return json.loads(raw)["content"]
    except: return raw
def trunc_payload(raw,n=256):
    t=raw[:n]; m=re.search(r'"content"\s*:\s*"(.*)$',t,re.S)
    return m.group(1) if m else ""
def value_present(g,text):
    return g.lower() in text.lower()

bench={i["index"]:i for i in json.load(open("benchmark_semantic.json"))}
resp=[json.loads(l) for l in open("mistral_responses.jsonl")]
results=[]
for r in resp:
    b=bench[r["index"]]; gts=list(b["pii"].values())
    raw=r["raw"]; full=full_content(raw); trunc=trunc_payload(raw)
    truly=any(value_present(g,full) for g in gts)
    results.append({"index":r["index"],"arm":b["arm"],"truly":truly,
        "meta":True,
        "dlp":len(detect_entities(full))>0,
        "klens":len(detect_entities(trunc))>0})

def metrics(key,subset=None):
    rows=subset if subset is not None else results
    tp=fp=fn=tn=0
    for x in rows:
        p=x[key]; t=x["truly"]
        if p and t: tp+=1
        elif p and not t: fp+=1
        elif not p and t: fn+=1
        else: tn+=1
    prec=tp/(tp+fp) if tp+fp else 0.0
    rec=tp/(tp+fn) if tp+fn else 0.0
    f1=2*prec*rec/(prec+rec) if prec+rec else 0.0
    return prec,rec,f1,(tp,fp,fn,tn)

print("=== RESPONSE-LEVEL LEAK DETECTION (n=%d) ==="%len(results))
print(f"{'Detector':<24}{'Precision':<11}{'Recall':<9}{'F1':<8}{'TP/FP/FN/TN'}")
summary={}
for name,key in [("Metadata-only (Falco)","meta"),("KLEnS (kernel, 256B)","klens"),("User-space DLP (full)","dlp")]:
    p,r,f,c=metrics(key); summary[key]=(p,r,f)
    print(f"{name:<24}{p:<11.3f}{r:<9.3f}{f:<8.3f}{c[0]}/{c[1]}/{c[2]}/{c[3]}")

print("\n=== PER-ARM RECALL: DLP(full) vs KLEnS(trunc) — truncation gap ===")
print(f"{'arm':<12}{'truly_leaks':<13}{'DLP(full)':<11}{'KLEnS(256B)':<12}")
for arm in ["structured","contextual","semantic"]:
    sub=[x for x in results if x["arm"]==arm]
    tl=sum(1 for x in sub if x["truly"])
    _,rd,_,_=metrics("dlp",sub); _,rk,_,_=metrics("klens",sub)
    print(f"{arm:<12}{tl:<13}{rd:<11.3f}{rk:<12.3f}")

json.dump(summary,open("baseline_summary.json","w"))

# ---- Figure 8 ----
dets=["Metadata-only\n(Falco)","KLEnS\n(kernel, 256B)","User-space DLP\n(full)"]
keys=["meta","klens","dlp"]
prec=[summary[k][0] for k in keys]; rec=[summary[k][1] for k in keys]
x=np.arange(len(dets)); w=0.35
fig,ax=plt.subplots(figsize=(8,5))
b1=ax.bar(x-w/2,prec,w,label="Precision",color="#2c7fb8")
b2=ax.bar(x+w/2,rec,w,label="Recall",color="#fc8d59")
for b in list(b1)+list(b2):
    ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.02,f"{b.get_height():.2f}",ha="center",fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(dets)
ax.set_ylabel("Response-level leak detection")
ax.set_ylim(0,1.15)
ax.set_title("Leak-detection: content-aware (KLEnS/DLP) vs metadata-only")
ax.legend(); ax.grid(axis="y",alpha=0.3)
plt.tight_layout(); plt.savefig("fig8_baseline.png",dpi=200)
print("\nwrote fig8_baseline.png")
