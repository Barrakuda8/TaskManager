DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS teams;
DROP TABLE IF EXISTS supports;
DROP TABLE IF EXISTS requests;
DROP TABLE IF EXISTS completed_chat;
DROP TYPE IF EXISTS request_status;
CREATE TYPE requests_status AS ENUM ('created', 'started', 'completed', 'canceled', 'delayed');

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
    lead_id BIGINT NULL,
    english BOOL DEFAULT FALSE,
    day_start TIME NULL,
    day_end TIME NULL,
    days_off INTEGER ARRAY NULL
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
    id BIGINT PRIMARY KEY NOT NULL UNIQUE,
    notification_time INTEGER NULL,
    notification_text TEXT NULL
)

