import json, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from presidio_analyzer import AnalyzerEngine
ENT=["EMAIL_ADDRESS","PHONE_NUMBER","PERSON","CREDIT_CARD"]; THR=0.4
an=AnalyzerEngine()
def detect(t):
    if not t: return []
    return [t[r.start:r.end] for r in an.analyze(text=t,language="en",entities=ENT,score_threshold=THR)]
def full_content(raw):
    try: return json.loads(raw)["content"]
    except: return raw
def trunc_content(raw,n=256):
    t=raw[:n]; m=re.search(r'"content"\s*:\s*"(.*)$',t,re.S)
    return m.group(1) if m else ""
def match_partial(gt,det):
    det=[d.lower() for d in det]; vl=gt.lower()
    return any(d==vl for d in det) or any(vl in d and len(vl)>=4 for d in det)
bench={i["index"]:i for i in json.load(open("benchmark_semantic.json"))}
resp=[json.loads(l) for l in open("mistral_responses.jsonl")]
acc={}
for r in resp:
    b=bench[r["index"]]; gts=list(b["pii"].values()); txt=full_content(r["raw"])
    for mode,det in [("full",detect(txt)),("trunc",detect(trunc_content(r["raw"])))]:
        for v in gts:
            s=acc.setdefault((b["arm"],mode),{"hit":0,"n":0}); s["n"]+=1; s["hit"]+=match_partial(v,det)
arms=["structured","contextual","semantic"]
def rec(a,m): s=acc.get((a,m),{"hit":0,"n":1}); return s["hit"]/max(s["n"],1)
full=[rec(a,"full") for a in arms]; trunc=[rec(a,"trunc") for a in arms]
x=np.arange(len(arms)); w=0.35
fig,ax=plt.subplots(figsize=(8,5))
b1=ax.bar(x-w/2,full,w,label="Full payload",color="#2c7fb8")
b2=ax.bar(x+w/2,trunc,w,label="Truncated (256 B)",color="#7fcdbb")
for b in list(b1)+list(b2):
    ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.02,f"{b.get_height():.2f}",ha="center",fontsize=9)
ax.set_xticks(x); ax.set_xticklabels(["Structured","Contextual","Semantic"])
ax.set_ylabel("Detection recall (partial match)")
ax.set_ylim(0,1.15)
ax.set_title("KLEnS detection recall by disclosure form and payload completeness")
ax.legend(); ax.grid(axis="y",alpha=0.3)
plt.tight_layout(); plt.savefig("fig7_semantic.png",dpi=200)
print("wrote fig7_semantic.png")
print("full :",[f"{v:.3f}" for v in full])
print("trunc:",[f"{v:.3f}" for v in trunc])
