# ChainProof Deployment Validation

Generated: 2026-10-03 by Cortex Code (claude-opus-4-6) (connection details omitted for public release).

---

## Created Objects

All objects in `SNOWFLAKE_LEARNING_DB.CHAINPROOF`:

| Object | Type | Query ID |
|---|---|---|
| CP_SHIPMENTS | TABLE | `01c77b75-0304-d160-0005-6fd60001d02a` |
| CP_ORDERS | TABLE | `01c77b75-0304-d160-0005-6fd60001d026` |
| CP_ALLOCATIONS | TABLE | `01c77b75-0304-d160-0005-6fd60001d01e` |
| CP_EVIDENCE | VIEW | `01c77b76-0304-d4cb-0005-6fd60001b4a6` |
| CP_ORDER_EXPOSURE | VIEW | `01c77b76-0304-d160-0005-6fd60001d046` |
| CP_EXPOSURE | SEMANTIC VIEW | `01c77b76-0304-d4cb-0005-6fd60001b4aa` |

Seed data: 3 shipments, 4 orders, 5 allocations.

---

## Errors and Repairs

### Personal database cannot hold tables

`CREATE TABLE` in `PERSONAL_DATABASE.CHAINPROOF` failed with:
> Tables cannot currently be created in a personal database.

**Repair:** Switched to `SNOWFLAKE_LEARNING_DB.CHAINPROOF`. Updated `deployment_context.sql` with a comment explaining the change. Dropped the empty `PERSONAL_DATABASE.CHAINPROOF` schema (query ID `01c77b77-0304-d160-0005-6fd60001d052`).

No other SQL compatibility issues were encountered. All functions (`GREATEST`, `DATEDIFF`, `IFF`, `COALESCE`, `NUMBER(18,0)`) and the `CREATE SEMANTIC VIEW` DDL worked without modification.

---

## Acceptance Checks

### Check 1: Exposed orders and value

```sql
SELECT SUM(IS_EXPOSED) EXPOSED_ORDERS, SUM(EXPOSED_VALUE_INR) EXPOSED_VALUE_INR
FROM CP_ORDER_EXPOSURE;
```

| EXPOSED_ORDERS | EXPOSED_VALUE_INR |
|---|---|
| 2 | 2000000 |

Query ID: `01c77b77-0304-d4cb-0005-6fd60001b4be`

**PASS** — matches expected 2 exposed orders, INR 2,000,000.

### Check 2: Semantic view query

```sql
SELECT * FROM SEMANTIC_VIEW(CP_EXPOSURE
  METRICS orders.exposed_order_value_inr, orders.exposed_order_count);
```

| EXPOSED_ORDER_VALUE_INR | EXPOSED_ORDER_COUNT |
|---|---|
| 2000000 | 2 |

Query ID: `01c77b77-0304-d160-0005-6fd60001d056`

**PASS** — semantic view returns the same totals.

### Check 3: Late evidence rows

```sql
SELECT * FROM CP_EVIDENCE WHERE LATE_DAYS > 0 ORDER BY ORDER_ID, SHIPMENT_ID;
```

| SHIPMENT_ID | ORDER_ID | SUPPLIER | PART | PLANT | CUSTOMER | ARRIVAL | NEEDED | LATE_DAYS |
|---|---|---|---|---|---|---|---|---|
| S-101 | O-201 | Aster Components | Control module | Pune | Northstar Mobility | 2026-10-09 | 2026-10-06 | 3 |
| S-102 | O-201 | Birch Precision | Valve assembly | Pune | Northstar Mobility | 2026-10-08 | 2026-10-06 | 2 |
| S-101 | O-202 | Aster Components | Control module | Pune | Harbor Machines | 2026-10-09 | 2026-10-07 | 2 |

Query ID: `01c77b77-0304-d4cb-0005-6fd60001b4b6`

**PASS** — exactly 3 evidence rows covering 2 unique orders (O-201, O-202).

---

## What-If Scenario: S-101 Arrives 2026-10-06

Read-only recomputation using CTEs (no source tables modified).

```sql
WITH hypothetical_shipments AS (
  SELECT ID, SUPPLIER, PART, PLANT,
    CASE WHEN ID = 'S-101' THEN '2026-10-06'::DATE ELSE ARRIVAL END AS ARRIVAL
  FROM CP_SHIPMENTS
),
hypothetical_evidence AS (
  SELECT S.ID SHIPMENT_ID, O.ID ORDER_ID, S.SUPPLIER, S.PART, S.PLANT,
    O.CUSTOMER, S.ARRIVAL, O.NEEDED,
    GREATEST(DATEDIFF('day', O.NEEDED, S.ARRIVAL), 0) LATE_DAYS
  FROM CP_ALLOCATIONS A
  JOIN hypothetical_shipments S ON S.ID = A.SHIPMENT_ID
  JOIN CP_ORDERS O ON O.ID = A.ORDER_ID
),
hypothetical_order_exposure AS (
  SELECT O.ID ORDER_ID, O.CUSTOMER, O.NEEDED, O.VALUE_INR,
    COALESCE(MAX(E.LATE_DAYS), 0) MAX_LATE_DAYS,
    IFF(COALESCE(MAX(E.LATE_DAYS), 0) > 0, O.VALUE_INR, 0) EXPOSED_VALUE_INR,
    IFF(COALESCE(MAX(E.LATE_DAYS), 0) > 0, 1, 0) IS_EXPOSED
  FROM CP_ORDERS O
  LEFT JOIN hypothetical_evidence E ON O.ID = E.ORDER_ID
  GROUP BY O.ID, O.CUSTOMER, O.NEEDED, O.VALUE_INR
)
SELECT ORDER_ID, CUSTOMER, VALUE_INR, MAX_LATE_DAYS, EXPOSED_VALUE_INR, IS_EXPOSED
FROM hypothetical_order_exposure ORDER BY ORDER_ID;
```

| ORDER_ID | CUSTOMER | VALUE_INR | MAX_LATE_DAYS | EXPOSED_VALUE_INR | IS_EXPOSED |
|---|---|---|---|---|---|
| O-201 | Northstar Mobility | 1200000 | 2 | 1200000 | 1 |
| O-202 | Harbor Machines | 800000 | 0 | 0 | 0 |
| O-203 | Meadow Equipment | 500000 | 0 | 0 | 0 |
| O-204 | Orion Manufacturing | 900000 | 0 | 0 | 0 |

Totals: **1 exposed order, INR 1,200,000.**

Query IDs: `01c77b77-0304-d4cb-0005-6fd60001b4ca` (detail), `01c77b77-0304-d160-0005-6fd60001d05e` (totals)

**PASS** — O-201 stays exposed (S-102 still arrives 2026-10-08, 2 days late vs needed 2026-10-06). O-202 recovers because S-101 now arrives 2026-10-06, which is before the 2026-10-07 needed date (DATEDIFF = -1, GREATEST(-1, 0) = 0).

---

## Negative Control: Naive Join Overcounting

```sql
SELECT SUM(O.VALUE_INR) AS NAIVE_TOTAL_INR
FROM CP_EVIDENCE E
JOIN CP_ORDERS O ON E.ORDER_ID = O.ID
WHERE E.LATE_DAYS > 0;
```

| NAIVE_TOTAL_INR |
|---|
| 3200000 |

Query ID: `01c77b78-0304-d4cb-0005-6fd60001b4d6`

### Why the naive join overcounts

The naive query joins late evidence rows directly to orders and sums `VALUE_INR`. Because O-201 has **two** late allocations (S-101 and S-102), its value of INR 1,200,000 appears in two joined rows. The sum becomes:

- O-201 row 1 (S-101): 1,200,000
- O-201 row 2 (S-102): 1,200,000
- O-202 row 1 (S-101): 800,000
- **Total: 3,200,000** (incorrect)

The governed `CP_ORDER_EXPOSURE` view avoids this by grouping to order grain first (`GROUP BY O.ID, ...`, taking `MAX(LATE_DAYS)`), which collapses multiple late allocations into one row per order before summing value:

- O-201: 1,200,000 (counted once)
- O-202: 800,000 (counted once)
- **Total: 2,000,000** (correct)

This deduplication design is the core of ChainProof's exposure calculation.

---

## Outstanding Limitations

- The deployment target was changed from `PERSONAL_DATABASE` (personal database) to `SNOWFLAKE_LEARNING_DB` because personal databases do not support table creation. The `deployment_context.sql` file was updated accordingly.
- The semantic view `CP_EXPOSURE` references `CP_ORDER_EXPOSURE` by unqualified name; it works within the same schema but would need fully qualified names if the view were referenced cross-schema.
- The fixture is a static demo snapshot with 3 shipments and 4 orders. No ongoing refresh or streaming ingestion is configured.
