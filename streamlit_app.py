import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
import streamlit as st
from engine import evaluate
from snowflake_backend import load_live, route_question

st.set_page_config(page_title='ChainProof · AICrew', page_icon='🔗', layout='wide')
st.title('ChainProof')
st.caption('AICrew · Supply Chain Ontology and Governed Conversational Analytics')
try:
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
except Exception:
    session = None

mode = st.sidebar.radio('Data source', ['Synthetic local demo', 'Live Snowflake'], index=1 if session else 0)
st.sidebar.caption('All business data in this project is synthetic, including the Snowflake tables.')
trace = []
if mode == 'Live Snowflake':
    if session is None:
        st.error('No Snowflake session. Open the app in Streamlit in Snowflake. The local demo remains available in the sidebar.')
        st.stop()
    try:
        data, governed, trace = load_live(session)
        baseline = evaluate(data)
        if (int(governed['EXPOSED_ORDER_VALUE_INR']), int(governed['EXPOSED_ORDER_COUNT']), int(governed['ORDER_COUNT'])) != (baseline['exposed_value_inr'], len(baseline['exposed_orders']), baseline['total_orders']):
            raise ValueError('Semantic-view totals and source evidence differ. Refresh and investigate before using the result.')
        st.success('Live Snowflake query complete. Semantic-view totals agree with source evidence.')
    except Exception as exc:
        st.error(f'Snowflake validation failed: {exc}')
        st.stop()
else:
    data = json.loads((Path(__file__).parent / 'data/demo.json').read_text(encoding='utf-8-sig'))
    baseline = evaluate(data)
    st.info('Local synthetic demo. Natural-language questions require Live Snowflake mode.')

if st.sidebar.button('Refresh data'):
    st.rerun()
st.sidebar.write('Snapshot: 3 October 2026')
st.sidebar.write('Currency: INR')
source_hash = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def pack(result):
    return json.dumps({'source':mode, 'synthetic':True, 'snapshot_date':data['snapshot_date'],
                       'generated_at':datetime.now(timezone.utc).isoformat(), 'source_sha256':source_hash,
                       'query_evidence':trace, 'result':result}, indent=2, default=str)

a,b,c = st.columns(3)
a.metric('Exposed order value', f"INR {baseline['exposed_value_inr']:,}")
b.metric('Exposed orders', len(baseline['exposed_orders']))
c.metric('Orders in scope', baseline['total_orders'])
st.caption(baseline['definition'])
ask, evidence, scenario, audit, definitions = st.tabs(['Ask ChainProof', 'Trace the evidence', 'Test an arrival scenario', 'Check double counting', 'Definitions & limits'])
with ask:
    st.subheader('Ask about the governed exposure metric')
    st.write('Try “What is the total exposed order value?” or “Why is Northstar Mobility exposed?”')
    model = st.text_input('Cortex model available in your account', 'claude-sonnet-4-5', help='The account must permit this model. A failed AI call does not fall back to a simulated answer.')
    question = st.text_input('Your question', max_chars=1000)
    if st.button('Answer with evidence', disabled=mode!='Live Snowflake'):
        try:
            customers = sorted({o['customer'] for o in data['orders']})
            route, question_ids = route_question(session, question, model, customers)
            if route['intent']=='unsupported':
                st.warning('This question is outside the supported exposure analysis or needs clarification. Ask about current exposure, evidence, metric definitions, or duplicate counting. Use the scenario tab for arrival changes.')
            else:
                selected = data if route['customer'] is None else {**data,
                    'orders':[o for o in data['orders'] if o['customer']==route['customer']],
                    'allocations':[x for x in data['allocations'] if x['order_id'] in {o['id'] for o in data['orders'] if o['customer']==route['customer']}]}
                answer = evaluate(selected)
                st.caption('Scope: '+(route['customer'] or 'all customers')+' · Intent: '+route['intent'])
                if route['intent']=='definition':
                    st.write(answer['definition'])
                elif route['intent']=='audit':
                    order_values={o['id']:o['value_inr'] for o in selected['orders']}
                    naive=sum(order_values[e['order_id']] for e in answer['evidence'])
                    st.write(f"An allocation-level sum gives INR {naive:,}. The unique-order calculation gives INR {answer['exposed_value_inr']:,}. The difference is INR {naive-answer['exposed_value_inr']:,}.")
                else:
                    st.write(f"{len(answer['exposed_orders'])} order(s) have late allocated inputs, exposing INR {answer['exposed_value_inr']:,} of order value.")
                st.dataframe(answer['evidence'], use_container_width=True)
                st.caption('AI interprets the question. Deterministic calculations supply every amount and evidence row.')
            st.write('Cortex query IDs:', question_ids)
        except Exception as exc:
            st.error(f'Question could not be answered: {exc}')
with evidence:
    st.subheader('Why these orders are exposed')
    st.dataframe(baseline['evidence'], use_container_width=True)
    st.download_button('Download baseline evidence', pack(baseline), 'chainproof-evidence.json', 'application/json')
with scenario:
    shipment = st.selectbox('Shipment to change', [s['id'] for s in data['shipments']])
    original = next(s for s in data['shipments'] if s['id']==shipment)
    arrival = st.date_input('Hypothetical arrival date', date.fromisoformat(original['arrival']), key=shipment)
    changed = evaluate(data, {shipment:arrival.isoformat()})
    st.metric('Scenario exposed order value', f"INR {changed['exposed_value_inr']:,}", f"{changed['exposed_value_inr']-baseline['exposed_value_inr']:+,} INR", delta_color='inverse')
    recovered=sorted(set(baseline['exposed_orders'])-set(changed['exposed_orders']))
    worsened=sorted(set(changed['exposed_orders'])-set(baseline['exposed_orders']))
    st.write('Orders no longer exposed:', ', '.join(recovered) or 'None')
    st.write('Newly exposed orders:', ', '.join(worsened) or 'None')
    st.dataframe(changed['evidence'], use_container_width=True)
    st.warning('Hypothetical arrival only. This does not book transport or change source tables. Reduced exposure is not guaranteed savings.')
    st.download_button('Download scenario evidence', pack({'assumptions':{shipment:arrival.isoformat()},'baseline':baseline,'scenario':changed}), 'chainproof-scenario.json', 'application/json')
with audit:
    values={o['id']:o['value_inr'] for o in data['orders']}
    naive=sum(values[e['order_id']] for e in baseline['evidence'])
    a,b=st.columns(2)
    a.metric('Naive allocation-level sum', f'INR {naive:,}')
    b.metric('Overstatement', f"INR {naive-baseline['exposed_value_inr']:,}")
    st.write('An order with two late inputs appears twice in a shipment join. ChainProof aggregates to one row per order before adding order value.')
    st.code('Late shipment allocations → unique order IDs → sum each order value once', language=None)
with definitions:
    st.markdown('''An order is exposed when **any explicitly allocated shipment arrives after its material-needed date**. Arrival on that date is on time. We count the full order value once.

The source links supplier, part and plant attributes through shipment allocations to orders and customers. The governed semantic view exposes order-level dimensions and metrics.

**Scope:** a fixed synthetic snapshot, INR, calendar dates, and explicit allocations. This MVP does not model inventory buffers, partial quantities, production capacity, ongoing ingestion, probability of failure, or actual revenue loss. The dataset contains no real enterprise or personal records.

**Question scope:** overall or one-customer exposure, evidence, definition, and duplicate-counting audit. AI output selects an allowed analysis and an existing customer. It never supplies executable SQL or numeric answers. Unsupported questions require clarification.''')
    st.write('Source fingerprint:', source_hash)
    if trace:
        st.json(trace)
