-- PostgreSQL schema for platform_db, functionally identical to schema.py

-- Challenges table
CREATE TABLE IF NOT EXISTS challenges (
    challenge_id TEXT PRIMARY KEY,  -- UUID for the challenge
    type TEXT NOT NULL CHECK(type IN ('codegen', 'regression')),
    validator_hotkey TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- Codegen challenges table
CREATE TABLE IF NOT EXISTS codegen_challenges (
    challenge_id TEXT PRIMARY KEY,
    problem_statement TEXT NOT NULL, -- Problem statement for codegen challenges
    dynamic_checklist TEXT NOT NULL,  -- Stored as JSON array
    repository_url TEXT NOT NULL,     -- URL of the repository
    commit_hash TEXT,                 -- Optional commit hash for codegen challenges
    context_file_paths TEXT NOT NULL, -- JSON array of file paths relative to repo root
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id) ON DELETE CASCADE
);

-- Regression challenges table
CREATE TABLE IF NOT EXISTS regression_challenges (
    challenge_id TEXT PRIMARY KEY,
    problem_statement TEXT NOT NULL, -- Problem statement for regression challenges
    repository_url TEXT NOT NULL,     -- URL of the repository
    commit_hash TEXT,                 -- Optional commit hash for regression challenges
    context_file_paths TEXT NOT NULL, -- JSON array of file paths relative to repo root
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id) ON DELETE CASCADE
);

-- Responses table
CREATE TABLE IF NOT EXISTS responses (
    challenge_id TEXT NOT NULL,  -- UUID for the problem
    miner_hotkey TEXT NOT NULL,
    node_id INTEGER,
    processing_time DOUBLE PRECISION,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    evaluated BOOLEAN DEFAULT FALSE,
    score DOUBLE PRECISION,
    evaluated_at TIMESTAMP,
    PRIMARY KEY (challenge_id, miner_hotkey),
    FOREIGN KEY (challenge_id) REFERENCES challenges(challenge_id)
);

-- Codegen responses table
CREATE TABLE IF NOT EXISTS codegen_responses (
    challenge_id TEXT NOT NULL,
    miner_hotkey TEXT NOT NULL,
    response_patch TEXT NOT NULL,
    PRIMARY KEY (challenge_id, miner_hotkey),
    FOREIGN KEY (challenge_id, miner_hotkey) REFERENCES responses(challenge_id, miner_hotkey)
);

-- Regression responses table
CREATE TABLE IF NOT EXISTS regression_responses (
    challenge_id TEXT NOT NULL,
    miner_hotkey TEXT NOT NULL,
    response_patch TEXT,  -- Nullable response patch for regression responses
    PRIMARY KEY (challenge_id, miner_hotkey),
    FOREIGN KEY (challenge_id, miner_hotkey) REFERENCES responses(challenge_id, miner_hotkey)
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    miner_hotkey TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    type TEXT NOT NULL,
    version INTEGER NOT NULL,
    elo INTEGER NOT NULL,
    num_responses INTEGER NOT NULL DEFAULT 0
);

-- Validator versions table
CREATE TABLE IF NOT EXISTS validator_versions (
    id SERIAL PRIMARY KEY,
    validator_hotkey TEXT NOT NULL,
    version TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Scores table
CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL, -- trueskill, float_grader, weight
    validator_hotkey TEXT NOT NULL,
    miner_hotkey TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    challenge_id TEXT DEFAULT NULL
); 
