-- Teacher country: auto-detected from WhatsApp phone prefix, or set via web UI.
-- Used to inject country context into LLM prompts for curriculum-relevant lessons.

ALTER TABLE teachers ADD COLUMN IF NOT EXISTS country text NOT NULL DEFAULT '';
