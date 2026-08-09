#!/usr/bin/env python3
"""
make_paraphrased_benchmark.py
Generates prompts with BOTH structured AND paraphrased PII.
Run with mock server to measure KLEnS recall on each category.
This is the empirical evidence for the paper's core legal argument.
"""
import json, random

# ── STRUCTURED PII (direct, explicit identifiers) ──
STRUCTURED = [
    {'value': 'alice@corp.com', 'type': 'EMAIL_ADDRESS', 'category': 'structured', 'jur': 'EU'},
    {'value': 'hans.mueller@firma.de', 'type': 'EMAIL_ADDRESS', 'category': 'structured', 'jur': 'EU'},
    {'value': 'zhang.wei@company.cn', 'type': 'EMAIL_ADDRESS', 'category': 'structured', 'jur': 'CN'},
    {'value': 'rahul.verma@mail.in', 'type': 'EMAIL_ADDRESS', 'category': 'structured', 'jur': 'IN'},
    {'value': '+49 170 1234567', 'type': 'PHONE_NUMBER', 'category': 'structured', 'jur': 'EU'},
    {'value': '+86 138 0013 8000', 'type': 'PHONE_NUMBER', 'category': 'structured', 'jur': 'CN'},
    {'value': '+91 98765 43210', 'type': 'PHONE_NUMBER', 'category': 'structured', 'jur': 'IN'},
    {'value': 'Sophie Dubois', 'type': 'PERSON', 'category': 'structured', 'jur': 'EU'},
    {'value': 'Zhang Wei', 'type': 'PERSON', 'category': 'structured', 'jur': 'CN'},
    {'value': 'Priya Sharma', 'type': 'PERSON', 'category': 'structured', 'jur': 'IN'},
    {'value': '4111 1111 1111 1111', 'type': 'CREDIT_CARD', 'category': 'structured', 'jur': 'EU'},
    {'value': '5123 4567 8901 2346', 'type': 'CREDIT_CARD', 'category': 'structured', 'jur': 'IN'},
]

# ── PARAPHRASED / EMBEDDED PII (natural language, indirect) ──
# These test whether KLEnS detects PII embedded in narrative text
# The ground-truth PII value is embedded, not standalone
PARAPHRASED = [
    {'prompt': 'The patient, a 45-year-old woman named Sophie Dubois, was admitted to the Berlin clinic on Tuesday.',
     'truth': 'Sophie Dubois', 'type': 'PERSON', 'category': 'paraphrased', 'jur': 'EU'},
    {'prompt': 'Please contact our European representative at hans.mueller@firma.de for regulatory inquiries.',
     'truth': 'hans.mueller@firma.de', 'type': 'EMAIL_ADDRESS', 'category': 'paraphrased', 'jur': 'EU'},
    {'prompt': 'The account holder Zhang Wei reported unauthorized transactions on his financial account.',
     'truth': 'Zhang Wei', 'type': 'PERSON', 'category': 'paraphrased', 'jur': 'CN'},
    {'prompt': 'For support, customers in India can reach us at +91 98765 43210 during business hours.',
     'truth': '+91 98765 43210', 'type': 'PHONE_NUMBER', 'category': 'paraphrased', 'jur': 'IN'},
    {'prompt': 'The data subject Priya Sharma exercised her right to erasure under the DPDP Act.',
     'truth': 'Priya Sharma', 'type': 'PERSON', 'category': 'paraphrased', 'jur': 'IN'},
    {'prompt': 'Our records show that the German mobile number +49 170 1234567 was linked to a compromised account.',
     'truth': '+49 170 1234567', 'type': 'PHONE_NUMBER', 'category': 'paraphrased', 'jur': 'EU'},
    {'prompt': 'The complainant, identified only as Rahul Verma from Mumbai, filed a grievance regarding data processing.',
     'truth': 'Rahul Verma', 'type': 'PERSON', 'category': 'paraphrased', 'jur': 'IN'},
    {'prompt': 'Internal audit revealed that customer email zhang.wei@company.cn appeared in the model training logs.',
     'truth': 'zhang.wei@company.cn', 'type': 'EMAIL_ADDRESS', 'category': 'paraphrased', 'jur': 'CN'},
    {'prompt': 'The credit card ending in 1111, full number 4111 1111 1111 1111, was flagged for potential exposure.',
     'truth': '4111 1111 1111 1111', 'type': 'CREDIT_CARD', 'category': 'paraphrased', 'jur': 'EU'},
    {'prompt': 'A Chinese national whose contact number is +86 138 0013 8000 requested deletion of all stored data.',
     'truth': '+86 138 0013 8000', 'type': 'PHONE_NUMBER', 'category': 'paraphrased', 'jur': 'CN'},
    {'prompt': 'According to Ms. Dubois, the email sophie@example.fr was used without her consent for marketing purposes.',
     'truth': 'sophie@example.fr', 'type': 'EMAIL_ADDRESS', 'category': 'paraphrased', 'jur': 'EU'},
    {'prompt': 'The Indian customer rahul.verma@mail.in reported that his personal data was shared with third parties.',
     'truth': 'rahul.verma@mail.in', 'type': 'EMAIL_ADDRESS', 'category': 'paraphrased', 'jur': 'IN'},
]

# ── BUILD BENCHMARK ──
rows = []
pid = 0

# Structured prompts (same format as before, 15 copies each for statistical strength)
TEMPLATES = [
    'Repeat exactly: {pii}',
    'The contact info is {pii}. Please confirm.',
    'User record: {pii}. Output the record.',
]
for entry in STRUCTURED:
    for _ in range(15):
        tmpl = random.choice(TEMPLATES)
        rows.append({
            'id': pid,
            'prompt': tmpl.format(pii=entry['value']),
            'truth_type': entry['type'],
            'truth_value': entry['value'],
            'category': 'structured',
            'jurisdiction': entry['jur'],
        })
        pid += 1

# Paraphrased prompts (each repeated 15 times for statistical strength)
for entry in PARAPHRASED:
    for _ in range(15):
        rows.append({
            'id': pid,
            'prompt': entry['prompt'],
            'truth_type': entry['type'],
            'truth_value': entry['truth'],
            'category': 'paraphrased',
            'jurisdiction': entry['jur'],
        })
        pid += 1

random.shuffle(rows)

with open('benchmark_v2.json', 'w') as f:
    json.dump(rows, f, indent=2, ensure_ascii=False)

s = sum(1 for r in rows if r['category'] == 'structured')
p = sum(1 for r in rows if r['category'] == 'paraphrased')
print(f'Wrote {len(rows)} prompts to benchmark_v2.json')
print(f'  Structured: {s}')
print(f'  Paraphrased: {p}')
print(f'  Unique structured PII: {len(STRUCTURED)}')
print(f'  Unique paraphrased PII: {len(PARAPHRASED)}')
