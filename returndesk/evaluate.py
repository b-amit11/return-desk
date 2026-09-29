import json
from .core import ROOT,workflow
from .hubspot import build_ticket_properties

def evaluate():
    cases=json.loads((ROOT/'data/cases.json').read_text());results=[]
    for name,message,expected in cases:
        r=workflow(message)
        results.append({'case':name,'expected':expected,'actual':r['decision']['status'],'passed':r['decision']['status']==expected})
    connector_checks=[]
    for name,message,expected in cases:
        result=workflow(message)
        allowed=expected in {'eligible','human_review'}
        try:
            payload=build_ticket_properties(result)
            passed=allowed and bool(payload['hs_ticket_subject']) and 'No refund has been issued' in payload['content']
        except ValueError:
            passed=not allowed
        connector_checks.append({'case':name,'expected_submission':allowed,'passed':passed})
    report={'mode':'offline parser and deterministic policy rules','passed':sum(x['passed'] for x in results),'total':len(results),'connector_evaluation':{'passed':sum(x['passed'] for x in connector_checks),'total':len(connector_checks),'cases':connector_checks,'note':'Uses a fake gateway; it does not create HubSpot tickets.'},'limitations':'Developer-authored cases. Does not measure LLM extraction accuracy, real store policy correctness, or business impact.','cases':results}
    (ROOT/'reports/evaluation.json').write_text(json.dumps(report,indent=2))
    return report
if __name__=='__main__':
    r=evaluate();print(json.dumps(r,indent=2));raise SystemExit(r['passed']!=r['total'])
