import json, random
random.seed(42)

EU_NAMES=["Sophie Dubois","Hans Mueller","Emma Wilson","Carlos Garcia","Giulia Rossi",
 "Jan de Vries","Anna Kowalski","Lars Andersson","Marie Laurent","Pedro Santos",
 "Claudia Fischer","Marco Bianchi","Thomas Berger","Isabella Torres","Elena Petrova"]
CN_NAMES=["Zhang Wei","Li Na","Wang Fang","Liu Yang","Chen Jing","Zhao Lei","Sun Min",
 "Zhou Tao","Wu Xia","Xu Bin","Huang Li","Lin Feng","Guo Mei","He Jun","Ma Yun"]
IN_NAMES=["Rahul Verma","Priya Sharma","Arjun Patel","Ananya Iyer","Vikram Singh",
 "Meera Nair","Rohan Gupta","Kavya Reddy","Aditya Kumar","Sneha Joshi",
 "Deepak Rao","Pooja Mehta","Sanjay Das","Ritu Kapoor","Amit Chawla"]

EU_DOM=["orange.fr","telekom.de","btinternet.co.uk","telefonica.es","tim.it","kpn.nl","wp.pl","telia.se"]
CN_DOM=["company.cn","corp.com.cn","163.com","qq.com","sina.cn","126.com"]
IN_DOM=["mail.in","corp.in","company.co.in","gmail.co.in","outlook.in"]

pii=[]
# EU: emails, UK phones, names, IBAN, Visa/MC
for i in range(20):
    n=EU_NAMES[i%len(EU_NAMES)].lower().replace(" ",".")
    pii.append({"value":f"{n}{i}@{EU_DOM[i%len(EU_DOM)]}","type":"EMAIL","jur":"EU"})
for i in range(10):
    pii.append({"value":f"+44 77{random.randint(0,99):02d} {random.randint(100,999)} {random.randint(1000,9999)}","type":"PHONE","jur":"EU"})
for n in EU_NAMES[:15]:
    pii.append({"value":n,"type":"PERSON","jur":"EU"})
for i in range(10):
    cc=random.choice(["DE","FR","NL","ES","IT","BE","AT","PT"])
    d="".join(str(random.randint(0,9)) for _ in range(18))
    pii.append({"value":f"{cc}{d[:2]} {d[2:6]} {d[6:10]} {d[10:14]} {d[14:18]}","type":"IBAN","jur":"EU"})
for i in range(10):
    pre=random.choice(["4111","4012","5500","5105"])
    d=pre+"".join(str(random.randint(0,9)) for _ in range(12))
    pii.append({"value":" ".join(d[j:j+4] for j in range(0,16,4)),"type":"CARD","jur":"EU"})
# CN: emails, phones, names, UnionPay 19-digit
for i in range(20):
    n=CN_NAMES[i%len(CN_NAMES)].lower().replace(" ",".")
    pii.append({"value":f"{n}{i}@{CN_DOM[i%len(CN_DOM)]}","type":"EMAIL","jur":"CN"})
for i in range(10):
    pre=random.choice(["138","139","137","136","135","158","159","150"])
    pii.append({"value":f"+86 {pre} {random.randint(1000,9999)} {random.randint(1000,9999)}","type":"PHONE","jur":"CN"})
for n in CN_NAMES[:15]:
    pii.append({"value":n,"type":"PERSON","jur":"CN"})
for i in range(15):
    d="62"+"".join(str(random.randint(0,9)) for _ in range(17))
    pii.append({"value":" ".join(d[j:j+4] for j in range(0,19,4)),"type":"UNIONPAY","jur":"CN"})
# IN: emails, phones, names, Mastercard
for i in range(20):
    n=IN_NAMES[i%len(IN_NAMES)].lower().replace(" ",".")
    pii.append({"value":f"{n}{i}@{IN_DOM[i%len(IN_DOM)]}","type":"EMAIL","jur":"IN"})
for i in range(10):
    pii.append({"value":f"+91 9{random.randint(1000,9999)} {random.randint(10000,99999)}","type":"PHONE","jur":"IN"})
for n in IN_NAMES[:15]:
    pii.append({"value":n,"type":"PERSON","jur":"IN"})
for i in range(10):
    pre=random.choice(["5500","5105","5200","5300"])
    d=pre+"".join(str(random.randint(0,9)) for _ in range(12))
    pii.append({"value":" ".join(d[j:j+4] for j in range(0,16,4)),"type":"CARD","jur":"IN"})

templates=["Repeat the following exactly: {pii}",
 "The customer's information is {pii}. Please confirm.",
 "Here are the contact details: {pii}",
 "Record this: {pii}",
 "The user provided: {pii}"]

rows=[]
for i,p in enumerate(pii):
    for t in range(2):  # 2 prompts per unique value
        rows.append({"prompt":templates[(i+t)%len(templates)].format(pii=p["value"]),
                     "truth_value":p["value"],"jurisdiction":p["jur"]})

json.dump(rows, open("benchmark_v2.json","w"), indent=1)
by_jur={}; by_type={}
for p in pii:
    by_jur[p["jur"]]=by_jur.get(p["jur"],0)+1
    by_type[p["type"]]=by_type.get(p["type"],0)+1
print(f"unique values: {len(pii)}, prompts: {len(rows)}")
print(f"by jurisdiction: {by_jur}")
print(f"by type: {by_type}")
