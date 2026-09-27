import json
import pytest
from returndesk.core import ROOT, Intake, connect, lookup, decide, workflow
CASES=json.loads((ROOT/'data/cases.json').read_text())
@pytest.mark.parametrize('name,message,expected',CASES,ids=[c[0] for c in CASES])
def test_labeled_case(name,message,expected):
    r=workflow(message)
    assert r['decision']['status']==expected
    assert [e['id'] for e in r['evidence']]==r['decision']['citations']
    assert 'This review has not issued a refund' in r['draft']

def test_ownership_and_parameterized_lookup():
    with connect() as db:
        assert lookup(db,'ORD-1007','cust-demo') is None
        assert lookup(db,"' OR 1=1 --",'cust-demo') is None
        assert lookup(db,'ORD-1007','cust-other') is not None
    r=workflow('ORD-1007 damaged')
    assert r['order'] is None and 'Private order' not in str(r)

def test_invalid_delivery():
    with connect() as db: order=lookup(db,'ORD-1001','cust-demo')
    order['delivered']='bad-date'
    assert decide(Intake(order_id='ORD-1001',reason='damaged'),order)['status']=='human_review'

def test_damage_window_wording():
    assert 'photo' in workflow('ORD-1001 damaged')['draft']
    assert 'exception' in workflow('ORD-1008 damaged')['draft']

def test_multiple_orders_rejected():
    with pytest.raises(ValueError):workflow('ORD-1001 and ORD-1002 damaged')

def test_no_order_mutation():
    with connect() as db:
        before=[tuple(r) for r in db.execute('SELECT * FROM orders')]
        workflow('ORD-1001 changed my mind unopened',db=db)
        assert before==[tuple(r) for r in db.execute('SELECT * FROM orders')]

def test_schema_rejects_extra_authorization():
    with pytest.raises(ValueError):Intake(order_id='ORD-1001',approved=True)
