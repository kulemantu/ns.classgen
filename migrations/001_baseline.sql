-- Baseline migration: marks the init.sql schema as tracked.
-- No-op — the schema is applied via docker-entrypoint-initdb.d on fresh databases.
SELECT 1;
