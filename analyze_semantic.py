import json, re
from presidio_analyzer import AnalyzerEngine
ENT=["EMAIL_ADDRESS","PHONE_NUMBER","PERSON","CREDIT_CARD"]; THR=0.4
an=AnalyzerEngine()
def detect(t):
    if not t: return []
    res=an.analyze(text=t,language="en",entities=ENT,score_threshold=THR)
    return [t[r.start:r.end] for r in res]
def full_content(raw):
    try: return json.loads(raw)["content"]
    except: return raw
def trunc_content(raw,n=256):
    t=raw[:n]; m=re.search(r'"content"\s*:\s*"(.*)$',t,re.S)
    return m.group(1) if m else ""
def match(gt,det):
    det=[d.lower() for d in det]; vl=gt.lower()
    e=any(d==vl for d in det); p=e or any(vl in d and len(vl)>=4 for d in det)
    return e,p
bench={i["index"]:i for i in json.load(open("benchmark_semantic.json"))}
resp=[json.loads(l) for l in open("mistral_responses.jsonl")]
stats={}
for r in resp:
    b=bench[r["index"]]; gts=list(b["pii"].values())
    txt=full_content(r["raw"])
    verbatim=any(v.lower() in txt.lower() for v in gts)
    for label,det in [("full",detect(txt)),("trunc256",detect(trunc_content(r["raw"])))]:
        for v in gts:
            e,p=match(v,det); s=stats.setdefault((b["arm"],label),{"E":0,"P":0,"N":0})
            s["N"]+=1; s["E"]+=e; s["P"]+=p
    k=(b["arm"],"verbatim"); stats.setdefault(k,{"N":0,"V":0}); stats[k]["N"]+=1; stats[k]["V"]+=verbatim
print(f"{'arm':<10}{'mode':<10}{'recall_exact':<14}{'recall_partial':<15}")
for arm in ["structured","contextual","semantic"]:
    for mode in ["full","trunc256"]:
        s=stats.get((arm,mode),{"E":0,"P":0,"N":0}); n=max(s["N"],1)
        print(f"{arm:<10}{mode:<10}{s['E']/n:<14.3f}{s['P']/n:<15.3f}")
for arm in ["structured","contextual","semantic"]:
    s=stats.get((arm,"verbatim"),{"N":0,"V":0})
    print(f"{arm:<10} verbatim-rate: {s['V']}/{s['N']}")
json.dump(stats,open("semantic_analysis.json","w"))
