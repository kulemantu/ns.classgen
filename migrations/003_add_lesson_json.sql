-- V4.1: Add lesson_json column for structured output (parallel to text columns).
-- Nullable — old rows have NULL, new rows with FF_STRUCTURED_OUTPUT get JSON.

ALTER TABLE homework_codes ADD COLUMN IF NOT EXISTS lesson_json jsonb DEFAULT NULL;
ALTER TABLE lesson_cache ADD COLUMN IF NOT EXISTS lesson_json jsonb DEFAULT NULL;
