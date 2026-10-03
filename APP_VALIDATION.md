# ChainProof Application Validation

Generated: 2026-10-03 by Cortex Code (claude-opus-4-6) (connection details omitted).

---

## Deployment Objects

| Object | Type | Location | Query ID |
|---|---|---|---|
| CP_APP_STAGE | STAGE | SNOWFLAKE_LEARNING_DB.CHAINPROOF | `01c77b83-0304-d160-0005-6fd60001d0ae` |
| CHAINPROOF_APP | STREAMLIT | SNOWFLAKE_LEARNING_DB.CHAINPROOF | `01c77b8f-0304-d4cb-0005-6fd60001b53a` |

### Uploaded Artifacts

| File | Size | Stage Path |
|---|---|---|
| streamlit_app.py | 8,398 | cp_app_stage/streamlit_app.py |
| engine.py | 2,384 | cp_app_stage/engine.py |
| snowflake_backend.py | 3,763 | cp_app_stage/snowflake_backend.py |
| environment.yml | 116 | cp_app_stage/environment.yml |
| data/demo.json | 1,059 | cp_app_stage/data/demo.json |

### App Configuration

| Property | Value |
|---|---|
| Root location | @SNOWFLAKE_LEARNING_DB.CHAINPROOF.CP_APP_STAGE |
| Main file | streamlit_app.py |
| Query warehouse | COMPUTE_WH |
| Title | ChainProof · AICrew |

---

## Unit Tests

All 13 tests passed (12 original + 1 added for markdown fence handling).

```
test_arrival_on_needed_date_is_on_time ... ok
test_missing_allocation_target_is_rejected ... ok
test_multiple_late_shipments_do_not_double_count_order_value ... ok
test_recovery_keeps_orders_with_other_late_inputs_exposed ... ok
test_scenario_does_not_change_source ... ok
test_unknown_scenario_target_is_rejected ... ok
test_existing_customer_is_preserved ... ok
test_extra_sql_field_is_rejected ... ok
test_malformed_model_response_fails ... ok
test_markdown_fenced_json_is_accepted ... ok
test_sql_in_place_of_intent_is_rejected ... ok
test_unknown_customer_is_rejected ... ok
test_unsupported_is_explicit ... ok
```

### S-101 Scenario (engine.py)

```python
evaluate(data, {'S-101': '2026-10-06'})
```
Result: `exposed_orders=['O-201'], exposed_value_inr=1200000, evidence=1 row`

**PASS** — matches expected O-201 exposed, INR 1,200,000.

---

## AI_COMPLETE Classification Tests

Model used: **claude-sonnet-4-5** (app default, confirmed available on this account).

### Test 1: Total exposure

Question: "What is the total exposed order value?"

| Field | Value |
|---|---|
| intent | exposure |
| customer | null |

Query ID: `01c77b81-0304-d160-0005-6fd60001d07a`

**PASS** — correctly classified as exposure for all customers.

### Test 2: Northstar Mobility evidence

Question: "Why is Northstar Mobility exposed?"

| Field | Value |
|---|---|
| intent | evidence |
| customer | Northstar Mobility |

Query ID: `01c77b81-0304-d4cb-0005-6fd60001b4fa`

**PASS** — correctly classified as evidence scoped to Northstar Mobility.

### Test 3: Duplicate-counting audit

Question: "Show the duplicate-counting audit for all customers"

| Field | Value |
|---|---|
| intent | audit |
| customer | null |

Query ID: `01c77b81-0304-d4cb-0005-6fd60001b4f6`

**PASS** — correctly classified as audit for all customers.

### Test 4: Unsupported request (predict revenue loss)

Question: "Predict the guaranteed revenue loss for next quarter"

| Field | Value |
|---|---|
| intent | unsupported |
| customer | null |

Query ID: `01c77b81-0304-d160-0005-6fd60001d086`

**PASS** — correctly rejected as unsupported.

---

## Repairs

### 1. Markdown code fence handling in `parse_route`

**Problem:** `claude-sonnet-4-5` wraps JSON responses in markdown code fences (`` ```json ... ``` ``). The original `parse_route` in `snowflake_backend.py` passed the raw response directly to `json.loads`, which fails on fenced output.

**Fix:** Updated `parse_route` to strip markdown code fences before JSON parsing. The fix:
- Detects strings starting with `` ``` ``
- Strips the opening fence line (including optional language tag)
- Strips the closing `` ``` ``
- Then parses the remaining JSON

**Files changed:** `snowflake_backend.py` (lines 32-41), `tests/test_router.py` (added `test_markdown_fenced_json_is_accepted`).

**Validation:** All 13 tests pass. All 4 AI classification tests return correct results through the repaired parser.

### 2. `ALTER STREAMLIT ... ADD LIVE VERSION FROM LAST` not supported

The deployment guide suggested this command, but it returned "Attached stage not exists." The app was created successfully with `CREATE STREAMLIT` and is accessible at its URL. The `ADD LIVE VERSION` step appears unnecessary for stage-based deployments — the app serves from the stage root location directly.

---

## Source Query Verification

The app's `load_live` function runs 4 queries against the deployed objects. All verified:

| Query | Result | Query ID |
|---|---|---|
| `SELECT * FROM ...CP_SHIPMENTS` | 3 rows | `01c77b91-0304-d160-0005-6fd60001d102` |
| `SELECT * FROM ...CP_ORDERS` | 4 rows | `01c77b91-0304-d160-0005-6fd60001d0f6` |
| `SELECT * FROM ...CP_ALLOCATIONS` | 5 rows | `01c77b91-0304-d160-0005-6fd60001d106` |
| `SELECT * FROM SEMANTIC_VIEW(CP_EXPOSURE ...)` | 1 row: 2M/2/4 | `01c77b91-0304-d4cb-0005-6fd60001b55a` |

### Semantic-view cross-check

The app validates that semantic-view totals agree with engine-computed evidence:

| Metric | Semantic View | Engine | Match |
|---|---|---|---|
| EXPOSED_ORDER_VALUE_INR | 2,000,000 | 2,000,000 | Yes |
| EXPOSED_ORDER_COUNT | 2 | 2 | Yes |
| ORDER_COUNT | 4 | 4 | Yes |

**PASS** — the app's integrity check would succeed.

---

## What Was Not Verified

- **UI rendering in browser:** No browser automation was available. The Streamlit app's visual layout, interactive widgets, tab navigation, and download buttons were not tested through a live browser session. All verification was done at the SQL and Python code level.
- **`ALTER STREAMLIT ADD LIVE VERSION`:** Failed with "Attached stage not exists." The app was created successfully and should be accessible, but the live version promotion step could not be confirmed.
- **In-app AI question flow end-to-end:** The AI_COMPLETE calls and `parse_route` were tested individually via SQL. The full Streamlit widget flow (text input → button click → display) was not tested through a browser.

---

## Limitations

- The app default model is `claude-sonnet-4-5`. If this model becomes unavailable on the account, the user must enter a different model name in the app's text input.
- The `data/demo.json` relative path is preserved on the stage (`cp_app_stage/data/demo.json`). The app uses `Path(__file__).parent / 'data/demo.json'` which resolves correctly in SiS.
- No external access integration is configured. The app does not make external network calls, so none is needed.
- The `snow` CLI was not available in this environment, so deployment was done via SQL (CREATE STAGE, PUT, CREATE STREAMLIT) rather than `snow streamlit deploy`.

## Subsequent browser check

The app startup failed with a package-resolution error for python==3.11. The local environment.yml now omits this pin. Redeployment and end-to-end browser testing remain pending. Successful SQL and classification tests do not establish successful app startup.
