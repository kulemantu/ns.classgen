-- Add updated_at columns and auto-update triggers to mutable tables.
-- Append-only tables (sessions, homework_codes, quiz_submissions, usage_log,
-- lesson_history) do not need updated_at.

-- 1. Reusable trigger function
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Add columns
ALTER TABLE teachers           ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();
ALTER TABLE subscriptions      ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();
ALTER TABLE lesson_cache       ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();
ALTER TABLE schools            ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();
ALTER TABLE push_subscriptions ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();
ALTER TABLE parent_subscriptions ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- 3. Attach triggers
DROP TRIGGER IF EXISTS trg_teachers_updated_at ON teachers;
CREATE TRIGGER trg_teachers_updated_at
    BEFORE UPDATE ON teachers FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_subscriptions_updated_at ON subscriptions;
CREATE TRIGGER trg_subscriptions_updated_at
    BEFORE UPDATE ON subscriptions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_lesson_cache_updated_at ON lesson_cache;
CREATE TRIGGER trg_lesson_cache_updated_at
    BEFORE UPDATE ON lesson_cache FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_schools_updated_at ON schools;
CREATE TRIGGER trg_schools_updated_at
    BEFORE UPDATE ON schools FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_push_subs_updated_at ON push_subscriptions;
CREATE TRIGGER trg_push_subs_updated_at
    BEFORE UPDATE ON push_subscriptions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS trg_parent_subs_updated_at ON parent_subscriptions;
CREATE TRIGGER trg_parent_subs_updated_at
    BEFORE UPDATE ON parent_subscriptions FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- 4. Grant permissions on _migrations table to classgen_api role
-- (runner creates it as postgres, but PostgREST shouldn't need it — belt-and-suspenders)
DO $$ BEGIN
  IF EXISTS (SELECT FROM pg_roles WHERE rolname = 'classgen_api') THEN
    GRANT SELECT ON _migrations TO classgen_api;
  END IF;
END $$;
