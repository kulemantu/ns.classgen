CREATE TABLE IF NOT EXISTS sessions (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  thread_id text NOT NULL,
  role text NOT NULL,
  content text NOT NULL,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS homework_codes (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  code text UNIQUE NOT NULL,
  thread_id text NOT NULL,
  lesson_content text NOT NULL,
  quiz_questions jsonb NOT NULL DEFAULT '[]',
  homework_block text NOT NULL DEFAULT '',
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS quiz_submissions (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  homework_code text NOT NULL REFERENCES homework_codes(code),
  student_name text NOT NULL,
  student_class text NOT NULL,
  answers jsonb NOT NULL DEFAULT '[]',
  score integer NOT NULL DEFAULT 0,
  total integer NOT NULL DEFAULT 0,
  created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);
