import json
from .core import ROOT,workflow

def evaluate():
    cases=json.loads((ROOT/'data/cases.json').read_text());results=[]
    for name,message,expected in cases:
        r=workflow(message)
        results.append({'case':name,'expected':expected,'actual':r['decision']['status'],'passed':r['decision']['status']==expected})
    report={'mode':'offline parser and deterministic policy rules','passed':sum(x['passed'] for x in results),'total':len(results),'limitations':'Developer-authored cases. Does not measure LLM extraction accuracy, real store policy correctness, or business impact.','cases':results}
    (ROOT/'reports/evaluation.json').write_text(json.dumps(report,indent=2))
    return report
if __name__=='__main__':
    r=evaluate();print(json.dumps(r,indent=2));raise SystemExit(r['passed']!=r['total'])
