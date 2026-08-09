import json, requests, time
items=json.load(open("benchmark_semantic.json"))
out=open("mistral_responses.jsonl","w")
for it in items:
    try:
        r=requests.post("http://127.0.0.1:8080/",json={"prompt":it["prompt"]},timeout=120)
        raw=r.text
    except Exception as e: raw=json.dumps({"content":f"[runner error] {e}"})
    out.write(json.dumps({"index":it["index"],"arm":it["arm"],"raw":raw})+"\n"); out.flush()
    print(it["index"],it["arm"],end=" ",flush=True)
    time.sleep(0.3)
print("\ndone")
