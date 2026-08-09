#!/usr/bin/env python3
"""KLEnS PII detection + EU/CN/IN obligation mapping (regex fallback)."""
import json, datetime, os, re
from presidio_analyzer import AnalyzerEngine

analyzer = AnalyzerEngine()

HIGH_RISK   = {'CREDIT_CARD', 'IBAN_CODE', 'MEDICAL_LICENSE', 'NRP'}
MEDIUM_RISK = {'EMAIL_ADDRESS', 'PHONE_NUMBER', 'PERSON', 'IP_ADDRESS'}

# DECISION: শুধু এই entity গুলো PII ধরা হবে (URL/bank/license noise বাদ)
ALLOWED_ENTITIES = ['EMAIL_ADDRESS', 'PHONE_NUMBER', 'PERSON', 'CREDIT_CARD']

# DECISION: 0.4 কম। 0.5/0.6 test করে precision/recall trade-off report করো
SCORE_THRESHOLD = 0.4

OBLIGATION_MAP = {
    'EMAIL_ADDRESS': {
        'EU': ['GDPR Art.5(1)(f) --- integrity & confidentiality breach',
               'GDPR Art.33 --- notify supervisory authority within 72h',
               'GDPR Art.34 --- notify data subject if high risk'],
        'CN': ['PIPL Art.51 --- failure of security obligation',
               'PIPL Art.57 --- notify regulator (CAC) immediately'],
        'IN': ['DPDP s.8(6) --- notify Data Protection Board of breach'],
    },
    'PHONE_NUMBER': {
        'EU': ['GDPR Art.5(1)(f) --- integrity & confidentiality breach',
               'GDPR Art.33 --- notify supervisory authority within 72h'],
        'CN': ['PIPL Art.51 --- security obligation',
               'PIPL Art.57 --- notify regulator'],
        'IN': ['DPDP s.8(6) --- notify DPB of breach'],
    },
    'PERSON': {
        'EU': ['GDPR Art.17 --- right to erasure',
               'GDPR Art.5(1)(c) --- data minimisation violation'],
        'CN': ['PIPL Art.47 --- deletion right triggered',
               'PIPL Art.51 --- security obligation'],
        'IN': ['DPDP s.12 --- right to erasure',
               'DPDP s.8(6) --- breach if unauthorized disclosure'],
    },
    'CREDIT_CARD': {
        'EU': ['GDPR Art.5(1)(f) --- integrity & confidentiality breach',
               'GDPR Art.33/34 --- mandatory breach notification (high risk)'],
        'CN': ['PIPL Art.28 --- sensitive personal info (financial)'],
        'IN': ['DPDP s.8(6) --- breach notification'],
    },
    '_DEFAULT': {
        'EU': ['GDPR Art.5(1)(f) --- review: potential breach'],
        'CN': ['PIPL Art.51 --- review: security obligation'],
        'IN': ['DPDP s.8(6) --- review: potential breach'],
    },
}


def classify_severity(entity_type):
    if entity_type in HIGH_RISK:   return 'HIGH'
    if entity_type in MEDIUM_RISK: return 'MEDIUM'
    return 'LOW'


def extract_content(payload: str):
    """content field বের করো — JSON ভালো হলে json.loads, কাটা হলে regex."""
    # প্রথমে ঠিক JSON চেষ্টা করো
    try:
        obj = json.loads(payload)
        return obj.get('content')
    except (json.JSONDecodeError, TypeError):
        pass
    # FALLBACK: JSON কাটা/ভাঙা — regex দিয়ে "content":"..." বের করো
    m = re.search(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', payload)
    if not m:
        return None
    raw = m.group(1)
    # escaped অংশ (\n, \") unescape করার চেষ্টা করো
    try:
        return json.loads('"' + raw + '"')
    except json.JSONDecodeError:
        return raw  # unescape fail করলে raw-ই দাও


def analyze(payload: str):
    text_to_scan = extract_content(payload)
    if not text_to_scan or not str(text_to_scan).strip():
        return []

    # guard: নিজের obligation-text scan কোরো না
    if 'GDPR Art.' in text_to_scan or 'PIPL Art.' in text_to_scan \
            or 'DPDP s.' in text_to_scan:
        return []

    results = analyzer.analyze(
        text=text_to_scan, language='en',
        score_threshold=SCORE_THRESHOLD,
        entities=ALLOWED_ENTITIES,
    )
    findings = []
    for r in results:
        ent = r.entity_type
        obligations = OBLIGATION_MAP.get(ent, OBLIGATION_MAP['_DEFAULT'])
        findings.append({
            'entity': ent,
            'score': round(r.score, 2),
            'value': text_to_scan[r.start:r.end],
            'severity': classify_severity(ent),
            'obligations': obligations,
        })
    return findings


LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'klens_events.jsonl')


def handle(pid: int, payload: str, syscall: str = '?', fd: int = 0):
    if len(payload.strip()) < 5:
        return
    findings = analyze(payload)
    if not findings:
        return
    event = {
        'ts': datetime.datetime.utcnow().isoformat() + 'Z',
        'pid': pid, 'syscall': syscall, 'fd': fd,
        'payload_len': len(payload), 'findings': findings,
    }
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(event) + '\n')

    sevs = set(x['severity'] for x in findings)
    top = 'HIGH' if 'HIGH' in sevs else 'MEDIUM' if 'MEDIUM' in sevs else 'LOW'
    ents = ', '.join(set(x['entity'] for x in findings))
    jurs = set()
    for f in findings:
        for j in f['obligations']:
            jurs.add(j)
    print(f'[{top}] PII egress via {syscall}(fd={fd}): {ents}')
    for j in sorted(jurs):
        obls = [o for f2 in findings for o in f2['obligations'].get(j, [])]
        if obls:
            print(f'  {j}: {" | ".join(obls)}')
