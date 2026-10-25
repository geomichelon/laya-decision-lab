import os
os.environ['LAYA_LAB_PRELOAD']='0'
import unittest
from fastapi.testclient import TestClient
from app import app
from domain import policy


def answers(confidence=.9, churn=.1, urgency=.2):
    return {'department':{'choice':'technical','confidence':confidence},
            'urgency':{'score':urgency,'confidence':confidence},
            'churn_risk':{'noul':churn,'confidence':confidence}}

class LabTests(unittest.TestCase):
    def test_policy_requires_all_signals_to_pass(self):
        self.assertEqual(policy(answers())['outcome'],'suggested_route')
        for a in [answers(confidence=.79),answers(churn=.5),answers(urgency=1.5)]:
            result=policy(a,.8)
            self.assertEqual(result['outcome'],'human_review')
            self.assertFalse(result['executes_actions'])
        self.assertEqual(policy(answers(confidence=.8),.8)['outcome'],'suggested_route')

    def test_one_low_confidence_is_not_hidden_by_the_average(self):
        a=answers(confidence=.99);a['urgency']['confidence']=.2
        self.assertEqual(policy(a)['minimum_confidence'],.2)
        self.assertEqual(policy(a)['outcome'],'human_review')

    def test_http_rejects_bad_input_without_model_load(self):
        with TestClient(app) as client:
            for body in [{'text':'  '},{'text':'x','threshold':1.1},{'text':'x','model':'unknown'},{'text':'x'*2001}]:
                self.assertEqual(client.post('/api/analyze',json=body).status_code,422)
            self.assertEqual(client.post('/api/analyze',json={'text':'x'},headers={'origin':'https://unrelated.example'}).status_code,403)
            self.assertEqual(client.get('/api/status',headers={'host':'unrelated.example'}).status_code,400)
            self.assertEqual(client.get('/api/config').status_code,200)

if __name__=='__main__':unittest.main()
