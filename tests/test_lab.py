import os
os.environ['LAYA_LAB_PRELOAD'] = '0'
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app import app
from domain import policy, compare_policies


def answers(confidence=.9, churn=.1, urgency=.2, action='information'):
    return {'department': {'choice': 'billing', 'confidence': confidence},
            'urgency': {'score': urgency, 'confidence': confidence},
            'churn_risk': {'noul': churn, 'confidence': confidence},
            'requested_action': {'choice': action, 'confidence': confidence}}


class LabTests(unittest.TestCase):
    def test_routing_does_not_grant_financial_approval(self):
        for action in ['refund', 'cancellation']:
            p = policy(answers(action=action), .8)
            self.assertEqual(p['routing']['status'], 'auto_route_candidate')
            self.assertTrue(p['action']['approval_required'])
            self.assertFalse(p['executes_actions'])

    def test_urgency_and_retention_do_not_block_routing(self):
        p = policy(answers(churn=.9, urgency=1.8))
        self.assertEqual(p['routing']['status'], 'auto_route_candidate')
        self.assertEqual(p['priority']['level'], 'High')
        self.assertTrue(p['retention']['flagged'])

    def test_uncertain_action_does_not_hide_known_team(self):
        a = answers(); a['requested_action']['confidence'] = .1
        p = policy(a)
        self.assertEqual(p['routing']['status'], 'auto_route_candidate')
        self.assertEqual(p['action']['status'], 'clarification_required')

    def test_threshold_boundary_and_confidence_not_probability(self):
        a = answers(confidence=.8)
        a['department']['probabilities'] = {'billing': .99}
        self.assertEqual(policy(a, .8)['routing']['status'], 'auto_route_candidate')
        self.assertEqual(policy(a, .81)['routing']['status'], 'routing_review')
        a['urgency']['confidence'] = .1
        self.assertTrue(policy(a)['priority']['needs_validation'])
        self.assertEqual(policy(a)['routing']['status'], 'auto_route_candidate')

    def test_unclear_request_always_needs_clarification(self):
        self.assertEqual(policy(answers(action='unclear'), 0)['action']['status'], 'clarification_required')

    def test_policy_comparison_preserves_predictions_and_approval(self):
        a = answers(confidence=.6, action='refund')
        p = compare_policies(a)
        self.assertEqual(p['conservative']['routing']['status'], 'routing_review')
        self.assertEqual(p['balanced']['routing']['status'], 'auto_route_candidate')
        self.assertTrue(all(v['action']['approval_required'] for v in p.values()))
        self.assertEqual(a['department']['confidence'], .6)

    def test_http_policy_never_calls_inference(self):
        with TestClient(app) as client, patch('app.engine.predict') as predict:
            response = client.post('/api/policy', json={'answers': answers(action='refund'), 'threshold': .2})
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()['inference_performed'])
            self.assertTrue(response.json()['policy']['action']['approval_required'])
            predict.assert_not_called()
            for data in [{'answers': {}, 'threshold': .5}, {'answers': answers(), 'threshold': 2}]:
                self.assertEqual(client.post('/api/policy', json=data).status_code, 422)

    def test_http_rejects_bad_input_and_unrelated_origins(self):
        with TestClient(app) as client:
            for body in [{'text': '  '}, {'text': 'x', 'threshold': 1.1}, {'text': 'x', 'model': 'unknown'}, {'text': 'x'*2001}]:
                self.assertEqual(client.post('/api/analyze', json=body).status_code, 422)
            for endpoint, body in [('/api/analyze', {'text': 'x'}), ('/api/policy', {'answers': answers(), 'threshold': .5})]:
                self.assertEqual(client.post(endpoint, json=body, headers={'origin': 'https://unrelated.example'}).status_code, 403)
            self.assertEqual(client.get('/api/status', headers={'host': 'unrelated.example'}).status_code, 400)
            self.assertEqual(len(client.get('/api/config').json()['samples']), 16)


if __name__ == '__main__':
    unittest.main()
