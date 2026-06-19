-- Ensure UTF-8 encoding for all connections
SET CLIENT_ENCODING TO 'UTF8';

-- For each table, ensure text columns are using UTF-8
-- This command verifies the server encoding
SELECT datname, encoding FROM pg_database WHERE datname = current_database();
