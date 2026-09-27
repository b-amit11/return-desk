from pathlib import Path
from streamlit.testing.v1 import AppTest

def test_review_workflow(monkeypatch):
 monkeypatch.setenv('GROQ_API_KEY','')
 app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py')).run()
 assert not app.exception
 app.button[0].click().run()
 assert not app.exception
 assert app.session_state.result['decision']['status']=='human_review'
 assert app.button[1].disabled

def test_public_demo_never_calls_live(monkeypatch):
 import returndesk.core as core
 def forbidden(*args,**kwargs):raise AssertionError('Public demo attempted live API')
 monkeypatch.setattr(core,'extract_live',forbidden)
 monkeypatch.setenv('GROQ_API_KEY','test-key-never-used')
 app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'public_app.py')).run()
 assert not app.exception
 assert len(app.radio)==0
 app.button[0].click().run()
 assert not app.exception
 assert app.session_state.result['mode']=='offline'
 monkeypatch.delenv('RETURNDESK_PUBLIC_DEMO',raising=False)
