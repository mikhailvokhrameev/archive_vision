CREATE TABLE files (
    file_id SERIAL PRIMARY KEY,
    file_path TEXT NOT NULL,         -- полный путь (или можно хранить отдельно base_path + относительный)
    file_name TEXT NOT NULL,
    file_extension VARCHAR(10) NOT NULL CHECK (file_extension ~ '^[a-zA-Z0-9]+$'),
    load_date TIMESTAMP DEFAULT now()
);
CREATE TABLE file_transcripts (
    transcript_id SERIAL PRIMARY KEY,
    file_id INT NOT NULL REFERENCES files(file_id) ON DELETE CASCADE,
    transcript_path TEXT NOT NULL,   -- путь до расшифровки
    wer JSONB,                       -- JSON с уверенностью по словам
    created_at TIMESTAMP DEFAULT now()
);