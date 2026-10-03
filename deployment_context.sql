-- ChainProof deployment context for AICrew.
-- Run once. Stop on errors; do not replace existing project objects.
-- REPAIR: PERSONAL_DATABASE is a personal database and cannot hold tables.
--         Using SNOWFLAKE_LEARNING_DB instead.
USE WAREHOUSE COMPUTE_WH;
CREATE SCHEMA IF NOT EXISTS SNOWFLAKE_LEARNING_DB.CHAINPROOF;
USE DATABASE SNOWFLAKE_LEARNING_DB;
USE SCHEMA CHAINPROOF;
ALTER SESSION SET STATEMENT_TIMEOUT_IN_SECONDS = 60;
ALTER SESSION SET QUERY_TAG = 'AICrew_ChainProof_hackathon';
