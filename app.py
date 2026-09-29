import os
import streamlit as st
from dotenv import load_dotenv
from returndesk.core import ROOT, POLICY, TODAY, workflow
from returndesk.hubspot import HubSpotError, HubSpotTicketClient, submit_for_human_review
PUBLIC_DEMO=os.getenv('RETURNDESK_PUBLIC_DEMO')=='1'
if not PUBLIC_DEMO: load_dotenv(ROOT/'.env')
st.set_page_config(page_title='ReturnDesk',page_icon='↩',layout='wide')
st.markdown('<style>.block-container{max-width:1200px;padding-top:2rem} h1{letter-spacing:-.04em}</style>',unsafe_allow_html=True)
st.title('ReturnDesk')
st.write('Turn a return request into a policy-backed recommendation your support team can review.')
with st.sidebar:
 st.header('Demo workspace')
 if PUBLIC_DEMO:
  mode='Offline examples'
  st.info('Public interactive demo · preset parsing, no live AI calls.')
 else:
  mode=st.radio('Intake engine',['Offline examples','Live AI'])
 st.caption('Fixed customer: cust-demo. This is simulated identity, not production authentication.')
 st.caption(f'Demo date: {TODAY}. Fictional store policy: {POLICY["version"]}. All order data is synthetic; prices are USD cents.')
 st.info('No messages are sent and no refunds are issued.')
examples=['ORD-1001 arrived damaged. Can I get a refund?','ORD-1002 changed my mind; item is unopened.','ORD-1003 changed my mind; item is unopened.','ORD-1004 arrived damaged.','ORD-1007 changed my mind unopened.']
choice=st.selectbox('Example request',examples)
message=st.text_area('Customer message',value=choice,max_chars=4000,key='message_'+choice)
context=(message,mode)
if st.session_state.get('context')!=context:
 st.session_state.pop('result',None);st.session_state.pop('reviewed',None);st.session_state.context=context
if st.button('Review request',type='primary',disabled=mode=='Live AI' and not os.getenv('GROQ_API_KEY')):
 st.session_state.pop('result',None);st.session_state.pop('reviewed',None)
 try:
  with st.spinner('Checking request and policy…'):st.session_state.result=workflow(message,'live' if mode=='Live AI' else 'offline')
 except Exception as exc:
  st.error('Request could not be processed ('+type(exc).__name__+'). Check configuration or retry later. No recommendation was created.')
if mode=='Live AI' and not os.getenv('GROQ_API_KEY'):st.warning('Add your Groq key to the local .env file to enable live extraction.')
r=st.session_state.get('result')
if r:
 left,right=st.columns([1,1])
 with left:
  st.subheader(r['decision']['status'].replace('_',' ').title())
  st.write(r['decision']['explanation'])
  st.markdown('**Extracted fields — verify against the message**');st.json(r['intake'])
  if r['order']:
   o=r['order'];st.write(f"{o['order_id']} · {o['item']} · ${o['amount_cents']/100:.2f}")
   st.caption(f"Status: {o['status']} | Delivered: {o['delivered']}")
 with right:
  st.subheader('Policy evidence')
  for e in r['evidence']:
   st.markdown(f"**[{e['id']}] {e['title']}**");st.write(e['text'])
 st.subheader('Response draft')
 draft=st.text_area('Edit before review',value=r['draft'],height=130,key='draft_'+str(context))
 acknowledged=st.checkbox('I checked the extracted fields, order, policy evidence, and response.',key='ack_'+str(context))
 if st.button('Mark reviewed locally',disabled=not acknowledged):st.session_state.reviewed=draft
 if st.session_state.get('reviewed')==draft:
  st.success('Marked reviewed in this browser session. Nothing has been sent or refunded.')
  st.download_button('Download reviewed draft',draft,file_name='reviewed-response.txt')
  if not PUBLIC_DEMO and os.getenv('HUBSPOT_PRIVATE_APP_TOKEN'):
   st.caption('Optional CRM handoff: creates one HubSpot sandbox ticket containing the deterministic decision and policy citations. It never issues a refund.')
   send_to_hubspot=st.checkbox('I approve creating this HubSpot sandbox ticket.',key='hubspot_ack_'+str(context))
   if st.button('Create HubSpot review ticket',disabled=not send_to_hubspot):
    try:
     receipt=submit_for_human_review(r,HubSpotTicketClient.from_environment())
     st.success(f"HubSpot review ticket created: {receipt['ticket_id']}")
    except (HubSpotError,ValueError) as exc:
     st.error(f"HubSpot ticket was not created: {exc}")
 with st.expander('Execution trace'):
  for step in r['trace']:st.write(step)
with st.expander('All demo policy clauses'):
 for c in POLICY['clauses']:st.write(f"[{c['id']}] {c['title']}: {c['text']}")
st.caption('Offline mode uses a limited keyword parser. Live mode uses Groq for extraction only; policy decisions and response wording are deterministic. Policy evidence is retrieved by exact clause ID, not vector search.')
