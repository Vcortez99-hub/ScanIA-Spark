-- Database initialization script for ScanIA

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create custom types
CREATE TYPE user_role AS ENUM ('admin', 'user', 'readonly');
CREATE TYPE scan_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE vulnerability_severity AS ENUM ('critical', 'high', 'medium', 'low', 'info');
CREATE TYPE report_type AS ENUM ('executive_summary', 'technical_detailed', 'compliance_report', 'vulnerability_list');

-- Create sequences
CREATE SEQUENCE IF NOT EXISTS scan_number_seq START 1000;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scans table
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    target_url VARCHAR(500) NOT NULL,
    scan_types JSONB NOT NULL DEFAULT '[]',
    status scan_status DEFAULT 'pending',
    options JSONB DEFAULT '{}',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    celery_job_id VARCHAR(255),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vulnerabilities table
CREATE TABLE IF NOT EXISTS vulnerabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    vulnerability_id VARCHAR(255) NOT NULL,
    cve_id VARCHAR(50),
    severity vulnerability_severity NOT NULL,
    cvss_score DECIMAL(3,1),
    cvss_base_score DECIMAL(3,1),
    cvss_temporal_score DECIMAL(3,1),
    cvss_environmental_score DECIMAL(3,1),
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    solution TEXT,
    affected_url VARCHAR(500) NOT NULL,
    evidence JSONB DEFAULT '{}',
    attack_vector VARCHAR(50),
    attack_complexity VARCHAR(50),
    privileges_required VARCHAR(50),
    user_interaction_required BOOLEAN DEFAULT false,
    network_accessible BOOLEAN DEFAULT false,
    internet_facing BOOLEAN DEFAULT false,
    authentication_required BOOLEAN DEFAULT true,
    exploit_available BOOLEAN DEFAULT false,
    exploit_maturity VARCHAR(50),
    patch_available BOOLEAN DEFAULT false,
    days_since_disclosure INTEGER,
    days_since_patch INTEGER,
    asset_criticality DECIMAL(3,2) DEFAULT 0.5,
    status VARCHAR(50) DEFAULT 'open',
    remediation_notes TEXT,
    is_false_positive BOOLEAN DEFAULT false,
    user_feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    report_type report_type NOT NULL,
    format VARCHAR(20) NOT NULL DEFAULT 'pdf',
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500),
    file_size INTEGER,
    status VARCHAR(50) DEFAULT 'generating',
    progress INTEGER DEFAULT 0,
    generated_at TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Conversations table (for chat)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    context JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages table (for chat)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- User sessions table
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scans_user_id_created_at ON scans(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_scan_id_severity ON vulnerabilities(scan_id, severity);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_cve_id ON vulnerabilities(cve_id) WHERE cve_id IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_scan_id_type ON reports(scan_id, report_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_id ON conversations(user_id, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id, created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_expires ON user_sessions(expires_at);

-- Full-text search indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_title_fts ON vulnerabilities USING gin(to_tsvector('portuguese', title));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulnerabilities_description_fts ON vulnerabilities USING gin(to_tsvector('portuguese', description));

-- Composite indexes for dashboard queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_scans_user_status_created ON scans(user_id, status, created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vulns_scan_severity_status ON vulnerabilities(scan_id, severity, status);

-- Create materialized view for dashboard stats
CREATE MATERIALIZED VIEW IF NOT EXISTS user_security_stats AS
SELECT 
    s.user_id,
    COUNT(DISTINCT s.id) as total_scans,
    COUNT(DISTINCT v.id) as total_vulnerabilities,
    COUNT(DISTINCT CASE WHEN v.severity = 'critical' THEN v.id END) as critical_vulns,
    COUNT(DISTINCT CASE WHEN v.severity = 'high' THEN v.id END) as high_vulns,
    COUNT(DISTINCT CASE WHEN v.severity = 'medium' THEN v.id END) as medium_vulns,
    COUNT(DISTINCT CASE WHEN v.severity = 'low' THEN v.id END) as low_vulns,
    COUNT(DISTINCT s.target_url) as unique_targets,
    AVG(v.cvss_score) as avg_cvss_score,
    MAX(s.created_at) as last_scan_date
FROM scans s
LEFT JOIN vulnerabilities v ON s.id = v.scan_id
WHERE s.created_at >= NOW() - INTERVAL '90 days'
GROUP BY s.user_id;

-- Create unique index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS user_security_stats_user_id_idx ON user_security_stats (user_id);

-- Create function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_user_security_stats()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY user_security_stats;
END;
$$ LANGUAGE plpgsql;

-- Create trigger function
CREATE OR REPLACE FUNCTION trigger_refresh_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Notify to refresh stats asynchronously
    PERFORM pg_notify('refresh_stats', 'user_security_stats');
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach triggers to relevant tables
DROP TRIGGER IF EXISTS scan_stats_refresh ON scans;
CREATE TRIGGER scan_stats_refresh
    AFTER INSERT OR UPDATE OR DELETE ON scans
    FOR EACH STATEMENT
    EXECUTE FUNCTION trigger_refresh_stats();

DROP TRIGGER IF EXISTS vuln_stats_refresh ON vulnerabilities;
CREATE TRIGGER vuln_stats_refresh
    AFTER INSERT OR UPDATE OR DELETE ON vulnerabilities
    FOR EACH STATEMENT
    EXECUTE FUNCTION trigger_refresh_stats();

-- Insert default admin user (password: admin123)
INSERT INTO users (email, password_hash, full_name, role) 
VALUES (
    'admin@scania.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LRcUs0/DDhJXK8HbS', -- password: admin123
    'Administrador ScanIA', 
    'admin'
) ON CONFLICT (email) DO NOTHING;

-- Insert sample test user (password: user123)
INSERT INTO users (email, password_hash, full_name, role) 
VALUES (
    'user@scania.com', 
    '$2b$12$X.oYQmpKJVHGnxb4sNEX8uU0yDPKr8zFHvJZXs8lX6QLQR6oYQmS6', -- password: user123
    'Usuário Teste', 
    'user'
) ON CONFLICT (email) DO NOTHING;