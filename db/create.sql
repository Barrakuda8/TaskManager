DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS supports;
DROP TABLE IF EXISTS requests;
DROP TYPE IF EXISTS request_status;
CREATE TYPE request_status AS ENUM ('created', 'completed', 'canceled');

CREATE TABLE admins (
    id BIGINT PRIMARY KEY NOT NULL UNIQUE,
    name VARCHAR(32)
);

CREATE TABLE supports (
    id BIGINT PRIMARY KEY NOT NULL UNIQUE,
    username VARCHAR(32)
);

CREATE TABLE requests (
    id SERIAL PRIMARY KEY NOT NULL UNIQUE,
    buyer_id VARCHAR(16),
    support VARCHAR(32),
    text TEXT,
    chat BIGINT,
    status request_status DEFAULT 'created',
    created_at TIMESTAMP DEFAULT (timezone('Europe/Moscow', now())),
    completed_at TIMESTAMP NULL
);

