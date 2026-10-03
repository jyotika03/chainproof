# Live browser validation — 3 October 2026

Tested the deployed Streamlit app after the environment.yml repair.

| Check | Actual result | Status |
|---|---|---|
| Startup | App Active; Live Snowflake selected | PASS |
| Source/semantic agreement | Success message displayed | PASS |
| Baseline | INR 2,000,000; 2 exposed orders; 4 in scope | PASS |
| S-101 arrival 2026-10-06 | INR 1,200,000; delta -800,000; O-202 no longer exposed; remaining evidence S-102/O-201 | PASS |
| Duplicate-counting tab | Naive INR 3,200,000; overstatement INR 1,200,000 | PASS |
| Total exposure question | The question could not be mapped to a supported analysis | FAIL |
| Northstar evidence question | The question could not be mapped to a supported analysis | FAIL |

Question flow repair is requested in REPAIR_QUESTION_FLOW.md. Standalone AI classifications are not sufficient evidence for the app integration. No final hackathon submission has been made.

## Final retest after question-flow repair

All four questions passed in the deployed browser UI:
- Total exposure: INR 2,000,000 / 2 orders. Query 01c77ba5-0304-d4cb-0005-6fd60001b72a.
- Northstar evidence: INR 1,200,000 / 1 order / 2 late shipment rows. Query 01c77ba6-0304-d4cb-0005-6fd60001b74e.
- Audit: INR 3,200,000 naive, INR 2,000,000 unique orders, INR 1,200,000 difference. Query 01c77ba6-0304-d4cb-0005-6fd60001b762.
- Guaranteed future revenue loss: explicitly rejected as unsupported. Query 01c77ba6-0304-d4cb-0005-6fd60001b776.

Earlier failures above are retained as repair history and are resolved by this retest. All 16 unit tests passed independently after the repair. Video recording and final submission remain pending.
