-- Validated deployment: see DEPLOYMENT_VALIDATION.md for results and query IDs.
-- Run in a dedicated hackathon database/schema selected by the participant.
-- No CREATE OR REPLACE: fail rather than overwrite pre-existing objects.
CREATE TABLE CP_SHIPMENTS (ID VARCHAR, SUPPLIER VARCHAR, PART VARCHAR, PLANT VARCHAR, ARRIVAL DATE);
CREATE TABLE CP_ORDERS (ID VARCHAR, CUSTOMER VARCHAR, NEEDED DATE, VALUE_INR NUMBER(18,0));
CREATE TABLE CP_ALLOCATIONS (SHIPMENT_ID VARCHAR, ORDER_ID VARCHAR);
INSERT INTO CP_SHIPMENTS VALUES
('S-101','Aster Components','Control module','Pune','2026-10-09'),
('S-102','Birch Precision','Valve assembly','Pune','2026-10-08'),
('S-103','Cedar Systems','Sensor kit','Chennai','2026-10-05');
INSERT INTO CP_ORDERS VALUES
('O-201','Northstar Mobility','2026-10-06',1200000),
('O-202','Harbor Machines','2026-10-07',800000),
('O-203','Meadow Equipment','2026-10-06',500000),
('O-204','Orion Manufacturing','2026-10-10',900000);
INSERT INTO CP_ALLOCATIONS VALUES
('S-101','O-201'),('S-102','O-201'),('S-101','O-202'),('S-103','O-203'),('S-101','O-204');

CREATE VIEW CP_EVIDENCE AS
SELECT S.ID SHIPMENT_ID, O.ID ORDER_ID, S.SUPPLIER, S.PART, S.PLANT,
 O.CUSTOMER, S.ARRIVAL, O.NEEDED, GREATEST(DATEDIFF('day', O.NEEDED, S.ARRIVAL),0) LATE_DAYS
FROM CP_ALLOCATIONS A JOIN CP_SHIPMENTS S ON S.ID=A.SHIPMENT_ID
JOIN CP_ORDERS O ON O.ID=A.ORDER_ID;

-- Collapse to order grain BEFORE summing value; joining value to allocations
-- would duplicate orders with more than one late input.
CREATE VIEW CP_ORDER_EXPOSURE AS
SELECT O.ID ORDER_ID, O.CUSTOMER, O.NEEDED, O.VALUE_INR,
 COALESCE(MAX(E.LATE_DAYS),0) MAX_LATE_DAYS,
 IFF(COALESCE(MAX(E.LATE_DAYS),0)>0, O.VALUE_INR,0) EXPOSED_VALUE_INR,
 IFF(COALESCE(MAX(E.LATE_DAYS),0)>0,1,0) IS_EXPOSED
FROM CP_ORDERS O LEFT JOIN CP_EVIDENCE E ON O.ID=E.ORDER_ID
GROUP BY O.ID,O.CUSTOMER,O.NEEDED,O.VALUE_INR;

CREATE SEMANTIC VIEW CP_EXPOSURE
 TABLES (orders AS CP_ORDER_EXPOSURE PRIMARY KEY (ORDER_ID))
 DIMENSIONS (
  orders.order_id AS ORDER_ID,
  orders.customer AS CUSTOMER,
  orders.material_needed_date AS NEEDED
 )
 METRICS (
  orders.exposed_order_value_inr AS SUM(EXPOSED_VALUE_INR)
   COMMENT='Full order value counted once when any allocated shipment is late. Exposure is not forecast loss.',
  orders.exposed_order_count AS SUM(IS_EXPOSED),
  orders.order_count AS COUNT(ORDER_ID)
 )
 COMMENT='Synthetic ChainProof snapshot, 2026-10-03. Calendar-day arrival risk; no stock buffers or loss forecast.';

-- Acceptance checks: 2 exposed orders and INR 2000000 exposure.
SELECT SUM(IS_EXPOSED) EXPOSED_ORDERS, SUM(EXPOSED_VALUE_INR) EXPOSED_VALUE_INR FROM CP_ORDER_EXPOSURE;
SELECT * FROM SEMANTIC_VIEW(CP_EXPOSURE METRICS orders.exposed_order_value_inr, orders.exposed_order_count);
-- Expected 3 evidence rows, representing 2 unique orders.
SELECT * FROM CP_EVIDENCE WHERE LATE_DAYS > 0 ORDER BY ORDER_ID,SHIPMENT_ID;
