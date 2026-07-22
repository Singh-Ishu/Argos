-- SQL DDL for Argos Supabase Database Initialization

-- 1. Create table for scenario execution logs
CREATE TABLE IF NOT EXISTS scenario_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id TEXT NOT NULL,
    corridor_name TEXT NOT NULL,
    closure_percentage DOUBLE PRECISION NOT NULL,
    duration_days INTEGER NOT NULL,
    metrics JSONB NOT NULL,
    executive_briefing TEXT NOT NULL,
    cascading_impacts JSONB NOT NULL,
    recommended_policy_directives JSONB NOT NULL,
    simulation_timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Index scenario_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_scenario_execution_logs_scenario_id ON scenario_execution_logs(scenario_id);

-- 2. Create table for caching threat scores
CREATE TABLE IF NOT EXISTS cached_threat_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    corridor_name TEXT UNIQUE NOT NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    threat_level TEXT NOT NULL,
    primary_driver TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Index corridor_name on threat scores
CREATE INDEX IF NOT EXISTS idx_cached_threat_scores_corridor ON cached_threat_scores(corridor_name);
