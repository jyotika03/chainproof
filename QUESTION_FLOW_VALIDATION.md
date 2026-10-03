# ChainProof Question Flow Validation

Generated: 2026-10-03 by Cortex Code (claude-opus-4-6) (connection details omitted).

---

## Root Cause

### Symptom

Both test questions failed in the live browser with:
> "The question could not be mapped to a supported analysis."

### Diagnosis

A Snowpark stored procedure (`_test_ai_route`) was created to inspect the exact Python type and value of `AI_COMPLETE`'s return within the Snowpark runtime — the same environment used by Streamlit-in-Snowflake.

**Finding:** `AI_COMPLETE` returns a JSON-encoded VARCHAR string. In the Snowpark Python runtime, the column value is a Python `str` whose first character is a literal `"` (double quote). The full value is a JSON string literal wrapping markdown-fenced JSON:

```
"```json\n{\n  \"intent\": \"exposure\",\n  \"customer\": null\n}\n```"
```

Diagnostic query ID: `01c77ba0-0304-d160-0005-6fd60001d1f2`

### Why parse_route failed

The original `parse_route` called `json.loads()` once. Because the raw value is a JSON string literal (starts/ends with `"`), `json.loads` correctly parses it — but produces a **Python string** (the decoded JSON string content), not a dict. The code then checked `isinstance(value, dict)` which was `False`, raising the ValueError.

The previous fence-stripping fix (from the earlier session) only checked `raw.startswith('```')`, which was `False` because the string starts with `"`. The fence-stripping never executed.

**Parsing trace:**

| Step | Value | Type |
|---|---|---|
| raw from Snowpark | `"```json\n{...}\n```"` | str (starts with `"`) |
| `raw.startswith('```')` | False (starts with `"`) | — |
| `json.loads(raw)` | `` ```json\n{...}\n``` `` | str (decoded JSON string) |
| `isinstance(value, dict)` | False | → **ValueError** |

The fix requires a second parse: after the first `json.loads` produces a string, strip fences from that string and parse again to extract the dict.

---

## Fix Applied

### snowflake_backend.py

Extracted fence-stripping into `_strip_fences()` and made `parse_route` attempt a second `json.loads` when the first parse yields a string:

```python
def _strip_fences(text):
    """Remove optional markdown code fences from a string."""
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1] if '\n' in text else text[3:]
        text = text.rsplit('```', 1)[0]
    return text

def parse_route(raw, customers):
    """Reject malformed or out-of-scope model output. It never becomes SQL."""
    if isinstance(raw, str):
        value = json.loads(_strip_fences(raw))
    else:
        value = raw
    if isinstance(value, str):
        value = json.loads(_strip_fences(value))
    # ... existing intent/customer validation unchanged
```

This handles three response shapes:
1. **Plain JSON dict** — `json.loads` returns a dict directly
2. **Markdown-fenced JSON** — fence stripping + `json.loads` returns a dict
3. **JSON-encoded string wrapping fenced JSON** (actual Snowpark behavior) — first `json.loads` returns a string, second pass strips fences and parses the dict

Strict validation (exact `{intent, customer}` keys, intent allowlist, customer allowlist) is unchanged. No arbitrary SQL or extra fields are accepted.

### tests/test_router.py

Added 3 regression tests for the actual Snowpark response shape:

| Test | Input shape | Expected result |
|---|---|---|
| `test_snowpark_json_encoded_fenced_response` | `"```json\n{...}\n```"` (JSON-encoded fenced) | Parses to `{intent: exposure, customer: null}` |
| `test_snowpark_json_encoded_plain_response` | `"{\"intent\":...}"` (JSON-encoded plain) | Parses to `{intent: evidence, customer: Northstar Mobility}` |
| `test_snowpark_double_encoded_extra_field_rejected` | JSON-encoded with extra `sql` field | Rejected (ValueError) |

---

## Unit Test Results

All 16 tests pass:

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
test_snowpark_double_encoded_extra_field_rejected ... ok
test_snowpark_json_encoded_fenced_response ... ok
test_snowpark_json_encoded_plain_response ... ok
test_sql_in_place_of_intent_is_rejected ... ok
test_unknown_customer_is_rejected ... ok
test_unsupported_is_explicit ... ok
----------------------------------------------------------------------
Ran 16 tests in 0.001s
OK
```

---

## Snowpark Live Question Tests

All 4 questions were tested end-to-end through the repaired `parse_route` inside a Snowpark stored procedure (`_test_all_routes`), executing the same `AI_COMPLETE` call and parameter binding used by the app.

Procedure call query ID: `01c77ba2-0304-d4cb-0005-6fd60001b6a2`

### Test 1: Total exposure

| Field | Value |
|---|---|
| Question | What is the total exposed order value? |
| Intent | exposure |
| Customer | null |
| Pass | Yes |
| AI query ID | `01c77ba2-0304-d4cb-0005-6fd60001b6b6` |

### Test 2: Northstar Mobility evidence

| Field | Value |
|---|---|
| Question | Why is Northstar Mobility exposed? |
| Intent | evidence |
| Customer | Northstar Mobility |
| Pass | Yes |
| AI query ID | `01c77ba2-0304-d4cb-0005-6fd60001b6ba` |

### Test 3: Duplicate-counting audit

| Field | Value |
|---|---|
| Question | Show the duplicate-counting audit for all customers |
| Intent | audit |
| Customer | null |
| Pass | Yes |
| AI query ID | `01c77ba2-0304-d4cb-0005-6fd60001b6be` |

### Test 4: Unsupported request

| Field | Value |
|---|---|
| Question | Predict the guaranteed revenue loss for next quarter |
| Intent | unsupported |
| Customer | null |
| Pass | Yes |
| AI query ID | `01c77ba2-0304-d4cb-0005-6fd60001b6c2` |

---

## Deployment Operations

### File upload

```sql
PUT 'file://...snowflake_backend.py' @CP_APP_STAGE/ AUTO_COMPRESS=FALSE OVERWRITE=TRUE;
```

| Field | Value |
|---|---|
| File | snowflake_backend.py |
| Size | 3,954 bytes (was 3,763) |
| Stage MD5 | 2e72e681933c78d7305ed94946eeab6b |
| Status | UPLOADED |
| Query ID | `01c77ba3-0304-d4cb-0005-6fd60001b6c6` |

### Stage verification

All 5 files present. `environment.yml` repair preserved (md5 `5878b108bd915d839bd80eaca646ba5a`).

Query ID: `01c77ba3-0304-d160-0005-6fd60001d222`

### App refresh

```sql
ALTER STREAMLIT CHAINPROOF_APP SET ROOT_LOCATION = '@SNOWFLAKE_LEARNING_DB.CHAINPROOF.CP_APP_STAGE';
```

Query ID: `01c77ba3-0304-d4cb-0005-6fd60001b6ca`

---

## Changed Files

| File | Change |
|---|---|
| snowflake_backend.py | Extracted `_strip_fences()` helper; `parse_route` now handles JSON-encoded string responses with a second parse pass |
| tests/test_router.py | Added 3 regression tests for Snowpark JSON-encoded response shapes |

No tables, grants, compute, or environment.yml were changed.

---

## Remaining Limitations

- **Browser testing not performed.** The fix was validated through a Snowpark stored procedure that replicates the exact runtime behavior (same `session.sql()` with bound params, same `as_dict()` conversion). Browser-level testing is deferred to the user.
- **AI model non-determinism.** The classification prompt uses `temperature=0`, but AI responses can still vary. The fix handles multiple response shapes (plain JSON, fenced JSON, JSON-encoded fenced JSON) to be resilient across model output variations.
- **No structured output mode.** The `claude-sonnet-4-5` model does not support `show_details` or `response_format` options. The double-encoding behavior (JSON string wrapping) is inherent to how `AI_COMPLETE` returns VARCHAR results in the Snowpark runtime.

---

