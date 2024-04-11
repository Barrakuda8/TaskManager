DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS supports;
DROP TABLE IF EXISTS requests;
DROP TABLE IF EXISTS completed_chat;
DROP TYPE IF EXISTS request_status;
CREATE TYPE request_status AS ENUM ('created', 'started', 'completed', 'canceled');

CREATE TABLE admins (
    id BIGINT PRIMARY KEY NOT NULL UNIQUE,
    name VARCHAR(32)
);

CREATE TABLE teams (
    name VARCHAR(32) PRIMARY KEY UNIQUE
);

CREATE TABLE supports (
    id BIGINT NOT NULL,
    username VARCHAR(32) PRIMARY KEY UNIQUE,
    team VARCHAR(32),
    lead_id BIGINT NULL
);

CREATE TABLE requests (
    id SERIAL PRIMARY KEY NOT NULL UNIQUE,
    buyer_id VARCHAR(16),
    support VARCHAR(32),
    text TEXT,
    chat BIGINT,
    status request_status DEFAULT 'created',
    created_at TIMESTAMP DEFAULT (timezone('Europe/Moscow', now())),
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL
);

CREATE TABLE completed_chat (
    id BIGINT PRIMARY KEY NOT NULL UNIQUE
)

