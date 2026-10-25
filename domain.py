"""Presentation policy and a transparent keyword baseline, independent of Laya."""
import re
import time


def policy(answers, threshold=0.8):
    confidence = min(float(a.get('confidence', 0)) for a in answers.values())
    churn = float(answers['churn_risk']['noul'])
    urgency = float(answers['urgency']['score'])
    reasons = []
    if confidence < threshold:
        reasons.append('Model confidence is below the review threshold.')
    if churn >= 0.5:
        reasons.append('The model flags an intention to cancel.')
    if urgency >= 1.5:
        reasons.append('The model flags a high-urgency request.')
    return {'outcome': 'human_review' if reasons else 'suggested_route',
            'reasons': reasons or ['All three model outputs pass this illustrative policy.'],
            'minimum_confidence': confidence, 'threshold': threshold,
            'department': answers['department']['choice'], 'executes_actions': False}


def baseline(text):
    start = time.perf_counter()
    lower = text.lower()
    department = 'other'
    for label, pattern in [('billing', r'charg|refund|invoice|subscription|cobran|cobrad|estorno|assinatura|fatura'),
                           ('technical', r'error|bug|outage|signing in|login|erro|falha|indispon'),
                           ('sales', r'pric|plan|demo|preço|compra')]:
        if re.search(pattern, lower):
            department = label
            break
    return {'department': department, 'elapsed_ms': round((time.perf_counter()-start)*1000, 3),
            'method': 'Ordered keyword rules: billing, technical, sales, other. No semantic inference.'}
