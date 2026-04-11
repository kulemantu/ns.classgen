-- Onboarding consent: tracks when a user accepted terms.
-- NULL = not yet onboarded, timestamp = accepted.

ALTER TABLE teachers ADD COLUMN IF NOT EXISTS onboarded_at timestamptz DEFAULT NULL;
