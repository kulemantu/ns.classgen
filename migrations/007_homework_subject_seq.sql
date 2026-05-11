-- Migration 007: per-(teacher, subject) counter for mnemonic homework codes.
--
-- The homework-code generator was producing 4 random uppercase letters + 2
-- random digits (e.g. ZQXJ73). The roadmap copy and dev-seed names had
-- drifted toward mnemonic codes (MATH42, BIO47, HIST21), so this migration
-- backs the new generator that derives a subject prefix + per-(teacher,
-- subject) sequence number, giving codes like MATH01 / MATH02 / ... that
-- a teacher can read at a glance.
--
-- Global UNIQUE on homework_codes.code is intentionally preserved -- the
-- generator checks collisions and bumps the sequence until a globally-free
-- code lands. Drops back to pure random when subject is unknown.

CREATE TABLE IF NOT EXISTS homework_subject_seq (
    teacher_phone text NOT NULL,
    subject_code  text NOT NULL,   -- 4-letter prefix: MATH, BIOL, PHYS, ...
    next_seq      int  NOT NULL DEFAULT 1,
    updated_at    timestamp with time zone NOT NULL DEFAULT timezone('utc'::text, now()),
    PRIMARY KEY (teacher_phone, subject_code)
);

-- The counter is hammered by every lesson generation; (teacher, subject)
-- index is the PK lookup. No additional indexes needed at this scale.

-- Atomic increment: takes the next available seq value and bumps the
-- counter for the next caller. Returns the value the caller should use.
--
-- INSERT path  : row didn't exist -> insert with next_seq=2, return 1
-- UPDATE path  : row existed      -> bump next_seq, return old next_seq
--
-- The "RETURNING next_seq - 1" trick lets both paths use the same return
-- expression: after INSERT, next_seq=2 -> 1; after UPDATE, new next_seq
-- (= old + 1) -> old. Atomic under concurrent calls via ON CONFLICT.
CREATE OR REPLACE FUNCTION next_homework_seq(
    p_teacher_phone text,
    p_subject_code  text
) RETURNS int AS $$
DECLARE
    v_seq int;
BEGIN
    INSERT INTO homework_subject_seq (teacher_phone, subject_code, next_seq)
    VALUES (p_teacher_phone, p_subject_code, 2)
    ON CONFLICT (teacher_phone, subject_code) DO UPDATE
        SET next_seq   = homework_subject_seq.next_seq + 1,
            updated_at = timezone('utc'::text, now())
    RETURNING next_seq - 1 INTO v_seq;
    RETURN v_seq;
END;
$$ LANGUAGE plpgsql;

-- Grant EXECUTE to the PostgREST-facing role. Matches the pattern used by
-- the other classgen_api privileges declared in init.sql.
GRANT EXECUTE ON FUNCTION next_homework_seq(text, text) TO classgen_api;
GRANT SELECT, INSERT, UPDATE ON TABLE homework_subject_seq TO classgen_api;
