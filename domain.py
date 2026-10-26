"""Deterministic operational policy; model predictions never execute actions."""
import re
import time

POLICY_PRESETS = {'conservative': .8, 'balanced': .5, 'exploratory': .2}
ACTION_LABELS = {'information': 'Provide information', 'refund': 'Review a refund request',
                 'cancellation': 'Review a cancellation request', 'technical_help': 'Investigate the issue',
                 'sales_inquiry': 'Prepare a sales response', 'unclear': 'Clarify the request'}


def policy(answers, threshold=0.8):
    department = answers['department']
    urgency = answers['urgency']
    action = answers['requested_action']
    churn = answers['churn_risk']
    route_ok = department['confidence'] >= threshold
    action_kind = action['choice']
    approval = action_kind in ('refund', 'cancellation')
    clarify = action_kind == 'unclear' or action['confidence'] < threshold
    action_status = 'approval_required' if approval else ('clarification_required' if clarify else 'assistance_suggested')
    priority = 'High' if urgency['score'] >= 1.5 else ('Medium' if urgency['score'] >= .5 else 'Low')
    attention = churn['noul'] >= .5
    trace = [
        {'stage': 'Routing', 'observed': department['confidence'], 'threshold': threshold,
         'reason': f"Department confidence {department['confidence']:.1%} {'meets' if route_ok else 'is below'} the {threshold:.0%} routing threshold."},
        {'stage': 'Priority', 'observed': urgency['score'], 'threshold': 1.5,
         'reason': f"Expected urgency {urgency['score']:.2f}/2 gives {priority.lower()} priority (medium >= 0.5; high >= 1.5). Priority does not block routing."},
        {'stage': 'Action', 'observed': action_kind, 'threshold': threshold,
         'reason': ('Refunds and cancellations require human approval regardless of confidence.' if approval else
                    'The action is unclear or its confidence is below the threshold; clarify it with a person.' if clarify else
                    'Informational or support assistance can be proposed without financial approval; nothing is executed.')},
        {'stage': 'Retention', 'observed': churn['noul'], 'threshold': .5,
         'reason': f"Cancellation signal {churn['noul']:.1%} {'adds' if attention else 'does not add'} a retention flag. This flag alone does not block routing."}
    ]
    return {'version': 2, 'threshold': threshold, 'department': department['choice'],
            'routing': {'status': 'auto_route_candidate' if route_ok else 'routing_review',
                        'team': department['choice'], 'confidence': department['confidence']},
            'priority': {'level': priority, 'score': urgency['score'], 'confidence': urgency['confidence'],
                         'needs_validation': urgency['confidence'] < threshold},
            'action': {'kind': action_kind, 'label': ACTION_LABELS[action_kind], 'status': action_status,
                       'confidence': action['confidence'], 'approval_required': approval},
            'retention': {'flagged': attention, 'probability': churn['noul'], 'confidence': churn['confidence']},
            'trace': trace, 'executes_actions': False}


def compare_policies(answers):
    return {name: policy(answers, value) for name, value in POLICY_PRESETS.items()}


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
