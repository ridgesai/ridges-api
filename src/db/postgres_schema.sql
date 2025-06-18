-- Agents table
CREATE TABLE agents (
    agent_id UUID PRIMARY KEY NOT NULL,
    miner_hotkey TEXT NOT NULL,
    latest_version_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL
);

-- Agent Versions table
CREATE TABLE agent_versions (
    version_id UUID PRIMARY KEY NOT NULL,
    agent_id UUID NOT NULL REFERENCES agents(agent_id),
    version_num INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    score FLOAT
);

-- Evaluation Runs table
CREATE TABLE evaluation_runs (
    run_id UUID PRIMARY KEY NOT NULL,
    version_id UUID NOT NULL REFERENCES agent_versions(version_id),
    validator_hotkey TEXT NOT NULL,
    swebench_instance_id TEXT NOT NULL,
    logs TEXT,
    response TEXT,
    pass_to_fail INT,
    fail_to_pass INT,
    solved BOOLEAN,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP
);
