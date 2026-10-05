CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Demo accounts matching the seeded transactions below (user 1 = full demo
-- data, user 2 = isolation-testing only). Both passwords are DemoPass123!
INSERT INTO users (id, email, password_hash) VALUES
(1, 'demo1@example.com', '$2b$12$4y4QWNlEs0ch/p6MjgeKduD0taWFkTK6t5mOdx8pPUAwq5uQ9WrR.'),
(2, 'demo2@example.com', '$2b$12$wm8u0.q1.MmnKro/EArwZuj.Nc1vZWnI5Dogl0mAc2v3efDJDY2JW');

-- Keep the SERIAL sequence past the ids we inserted explicitly above.
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    merchant TEXT NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    category TEXT NOT NULL,
    transaction_date DATE NOT NULL
);

INSERT INTO transactions
(user_id, merchant, amount, currency, category, transaction_date)
VALUES
(1, 'Apple', 1500, 'EUR', 'electronics', '2026-08-03'),
(1, 'NVIDIA', 600, 'EUR', 'electronics', '2026-08-05'),
(1, 'Restaurant Bella', 80, 'EUR', 'restaurant', '2026-08-07'),
(1, 'Amazon', 120, 'EUR', 'electronics', '2026-08-10'),
(1, 'Supermarket', 250, 'EUR', 'groceries', '2026-08-12'),
(1, 'Swimming Pool', 100, 'EUR', 'sport', '2026-08-15'),
(1, 'Restaurant Roma', 60, 'EUR', 'restaurant', '2026-08-20'),
(1, 'Hotel', 300, 'EUR', 'travel', '2026-08-25'),

(1, 'Restaurant Tokyo', 90, 'EUR', 'restaurant', '2026-07-05'),
(1, 'Amazon', 200, 'EUR', 'electronics', '2026-07-10'),
(1, 'Supermarket', 180, 'EUR', 'groceries', '2026-07-15');

INSERT INTO transactions
(user_id, merchant, amount, currency, category, transaction_date)
VALUES
(2, 'Apple', 3000, 'EUR', 'electronics', '2026-08-03');

-- RAG document chunks. user_id NULL = shared app knowledge (seeded by
-- seed_documents.py, which also computes the real embeddings - this file
-- only defines the shape, it can't generate vectors on its own).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    source TEXT NOT NULL,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL
);
