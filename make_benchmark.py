#!/usr/bin/env python3
"""Generate PII benchmark prompts with ground truth for 3 jurisdictions."""
import json, random

# EU PII patterns
EU_PII = [
{'type':'EMAIL_ADDRESS','value':'hans.mueller@firma.de','jurisdiction':'EU'},
{'type':'EMAIL_ADDRESS','value':'sophie@example.fr','jurisdiction':'EU'},
{'type':'PHONE_NUMBER','value':'+44 7700 900123','jurisdiction':'EU'},
{'type':'PHONE_NUMBER','value':'+49 170 1234567','jurisdiction':'EU'},
{'type':'PERSON','value':'Hans Mueller','jurisdiction':'EU'},
{'type':'PERSON','value':'Sophie Dubois','jurisdiction':'EU'},
{'type':'CREDIT_CARD','value':'4111 1111 1111 1111','jurisdiction':'EU'},
{'type':'IBAN_CODE','value':'DE89 3704 0044 0532 0130 00','jurisdiction':'EU'},
]

# CN PII patterns
CN_PII = [
{'type':'EMAIL_ADDRESS','value':'zhang.wei@company.cn','jurisdiction':'CN'},
{'type':'PHONE_NUMBER','value':'+86 138 0013 8000','jurisdiction':'CN'},
{'type':'PERSON','value':'Zhang Wei','jurisdiction':'CN'},
{'type':'PERSON','value':'Li Na','jurisdiction':'CN'},
{'type':'CREDIT_CARD','value':'6222 0200 1234 5678 901','jurisdiction':'CN'},
]

# IN PII patterns
IN_PII = [
{'type':'EMAIL_ADDRESS','value':'rahul.verma@mail.in','jurisdiction':'IN'},
{'type':'PHONE_NUMBER','value':'+91 98765 43210','jurisdiction':'IN'},
{'type':'PHONE_NUMBER','value':'+91 11 2345 6789','jurisdiction':'IN'},
{'type':'PERSON','value':'Rahul Verma','jurisdiction':'IN'},
{'type':'PERSON','value':'Priya Sharma','jurisdiction':'IN'},
{'type':'CREDIT_CARD','value':'5123 4567 8901 2346','jurisdiction':'IN'},
]

ALL_PII = EU_PII + CN_PII + IN_PII

TEMPLATES = [
'Repeat exactly: {pii}',
'The contact info is {pii}. Please confirm.',
'User record: name={pii}. Output the record.',
'Here is the data: {pii}. Summarize it.',
'Customer {pii} filed a complaint. Details?',
]

rows = []
for i in range(300):
    entry = random.choice(ALL_PII)
    tmpl = random.choice(TEMPLATES)
    rows.append({
        'id': i,
        'prompt': tmpl.format(pii=entry['value']),
        'truth_type': entry['type'],
        'truth_value': entry['value'],
        'jurisdiction': entry['jurisdiction'],
    })

with open('benchmark.json','w') as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)
print(f'Wrote {len(rows)} benchmark prompts to benchmark.json')
