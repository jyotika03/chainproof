# ChainProof

**AICrew · Jyotika Tewari · Snowflake CoCo CLI Hackathon, GCC Edition**

ChainProof explains which customer orders depend on late shipments, counts exposed order value once per order, and tests hypothetical shipment arrivals. Every result includes the source identifiers needed to inspect the calculation.

## Verified result

In the synthetic fixture, two late inputs affect the same order. Summing full order value across the late-allocation join reports **INR 3,200,000**. The governed order-grain calculation correctly reports **INR 2,000,000 across two orders**. The naive approach overstates exposure by **60%**.

Moving S-101's arrival to 6 October reduces exposure to **INR 1,200,000**. O-202 recovers, but O-201 remains exposed because S-102 is still late. This is a hypothetical reduction in exposure, not guaranteed savings or predicted revenue loss.

The data model and these acceptance checks have been executed in Snowflake through CoCo CLI. See [deployment evidence](DEPLOYMENT_VALIDATION.md) for actual SQL, outputs, and query IDs. The live application deployment and AI runtime validation remain in progress until APP_VALIDATION.md records them. No hackathon submission has been made yet.

## Run the local demonstration

Requires Python 3.11 or later.

```
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Local mode uses only synthetic JSON data and deterministic calculations. It does not simulate an AI response. Natural-language questions are enabled only with an active Snowflake session.

## Three CLI capabilities

```
python chainproof_cli.py diagnose
python chainproof_cli.py audit
python chainproof_cli.py simulate --shipment S-101 --arrival 2026-10-06
python -m unittest discover -s tests -v
```

Use `--output path.json` to save an evidence report. Reports include a source fingerprint and timestamp. CoCo can invoke these commands and inspect their real output during the required recording.

## Snowflake setup

The validated deployment uses `SNOWFLAKE_LEARNING_DB.CHAINPROOF` and the existing `COMPUTE_WH`. `deployment_context.sql` records that context. Change it deliberately for another account and update `PREFIX` in `snowflake_backend.py` and the identifiers in `snowflake.yml` to match.

1. Select a dedicated schema and an appropriate role. Use an existing small warehouse.
2. Run the deployment context, then `snowflake_setup.sql` once. The script deliberately avoids replacing existing tables. Do not rerun the seed INSERTs against populated tables.
3. Run the acceptance queries and compare them with the fixture results above.
4. Deploy the listed app files using `snowflake.yml` or the equivalent Streamlit-in-Snowflake stage workflow. `environment.yml` declares the Snowflake runtime dependencies.
5. Open the app, select Live Snowflake, and verify that its semantic-view totals agree with source evidence. A mismatch stops the app.

A Snowflake-hosted app requires account access. Provide the public source repository and the recorded workflow for judges who cannot access the account.

## Question flow

The proposed live question path calls Snowflake AI_COMPLETE to choose a bounded analysis: exposure, evidence, metric definition, or duplicate-counting audit. The response may optionally choose one existing customer. The application validates that output and calculates the answer from retrieved source records. It never executes model-generated SQL or uses model-generated amounts.

Examples:

- What is the total exposed order value?
- Why is Northstar Mobility exposed?
- Why does a naive join overstate exposure?

Unsupported requests, unknown customers, malformed model output, unavailable AI models, and forecasting questions produce an explicit error or clarification. There is no silent fallback to a fabricated live answer. Live model availability and these routes must be confirmed in APP_VALIDATION.md before representing the AI flow as verified.

## Model and definitions

`CP_SHIPMENTS` carries supplier, part, plant and expected-arrival attributes. `CP_ORDERS` carries customer, material-needed date and full order value. `CP_ALLOCATIONS` expresses their many-to-many relationship.

`CP_EVIDENCE` calculates lateness for each allocation. `CP_ORDER_EXPOSURE` collapses to one row per order. `CP_EXPOSURE` publishes governed order dimensions and exposure metrics as a Snowflake semantic view.

An order is exposed if at least one allocated shipment arrives **after** its material-needed date. Arrival on that date is on time. All values use INR and calendar dates.

## Limits

This is a deliberately small synthetic snapshot dated 3 October 2026: 3 shipments, 4 orders and 5 explicit allocations. It does not model partial quantities, inventory buffers, production capacity, ingestion refresh, probabilities or actual revenue loss. Supplier, part and plant are attributes, not independently governed master-data entities in this MVP. Full row-level access policies and multi-user production hardening remain future work. No customer time savings or operational outcomes have been measured.

## CoCo development evidence

- Read-only compatibility checks were performed through CoCo; private session metadata is omitted.
- `DEPLOYMENT_VALIDATION.md`: actual deployment and acceptance results.
- `APP_VALIDATION.md`: live app results, once completed.

No credentials belong in this repository. Do not publish the private work directory, connection settings, or raw authentication logs.

## References

- [Official GCC challenge](https://hack2skill.com/event/cococlihack-gccedition/)
- [CoCo CLI](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [Snowflake semantic views](https://docs.snowflake.com/en/user-guide/views-semantic/example)
- [AI_COMPLETE](https://docs.snowflake.com/en/sql-reference/functions/ai_complete-single-string)
