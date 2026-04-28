-- Supported countries reference table — drives the profile dropdown.
-- Source of truth in prod; src/classgen/i18n.py mirrors it for the
-- in-memory fallback path (tests, local dev without DB). Tests assert
-- the two stay in sync.

CREATE TABLE IF NOT EXISTS supported_countries (
    name text PRIMARY KEY,
    flag text NOT NULL,
    region text NOT NULL,
    sort_order integer NOT NULL
);

GRANT SELECT ON supported_countries TO classgen_api;

-- Seed the 14 markets ClassGen actively supports. Ordering: regions in
-- East Africa, West Africa, Southern Africa, Other order; alphabetical
-- within each region.
INSERT INTO supported_countries (name, flag, region, sort_order) VALUES
    ('Kenya',          E'\xF0\x9F\x87\xB0\xF0\x9F\x87\xAA', 'East Africa',     1),
    ('Rwanda',         E'\xF0\x9F\x87\xB7\xF0\x9F\x87\xBC', 'East Africa',     2),
    ('Tanzania',       E'\xF0\x9F\x87\xB9\xF0\x9F\x87\xBF', 'East Africa',     3),
    ('Uganda',         E'\xF0\x9F\x87\xBA\xF0\x9F\x87\xAC', 'East Africa',     4),
    ('Cameroon',       E'\xF0\x9F\x87\xA8\xF0\x9F\x87\xB2', 'West Africa',     5),
    ('Ghana',          E'\xF0\x9F\x87\xAC\xF0\x9F\x87\xAD', 'West Africa',     6),
    ('Nigeria',        E'\xF0\x9F\x87\xB3\xF0\x9F\x87\xAC', 'West Africa',     7),
    ('Botswana',       E'\xF0\x9F\x87\xA7\xF0\x9F\x87\xBC', 'Southern Africa', 8),
    ('South Africa',   E'\xF0\x9F\x87\xBF\xF0\x9F\x87\xA6', 'Southern Africa', 9),
    ('Zambia',         E'\xF0\x9F\x87\xBF\xF0\x9F\x87\xB2', 'Southern Africa', 10),
    ('Zimbabwe',       E'\xF0\x9F\x87\xBF\xF0\x9F\x87\xBC', 'Southern Africa', 11),
    ('India',          E'\xF0\x9F\x87\xAE\xF0\x9F\x87\xB3', 'Other',           12),
    ('United Kingdom', E'\xF0\x9F\x87\xAC\xF0\x9F\x87\xA7', 'Other',           13),
    ('United States',  E'\xF0\x9F\x87\xBA\xF0\x9F\x87\xB8', 'Other',           14)
ON CONFLICT (name) DO NOTHING;
