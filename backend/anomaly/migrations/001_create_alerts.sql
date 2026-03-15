-- Phase 4: Anomaly Detection Engine
-- Create alerts and alert_thresholds tables

-- Alerts table: stores detected anomalies and trends
CREATE TABLE IF NOT EXISTS alerts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at   TIMESTAMP DEFAULT now(),
    severity     VARCHAR(10) CHECK (severity IN ('critical', 'warning', 'info')),
    alert_type   VARCHAR(30) CHECK (alert_type IN ('spike', 'trend', 'duplicate', 'vendor', 'timing')),
    category     VARCHAR(50) NOT NULL,
    amount       DECIMAL(12,2) NOT NULL,
    baseline     DECIMAL(12,2),
    delta_pct    DECIMAL(6,2),
    period_start DATE,
    period_end   DATE,
    description  TEXT,
    runway_impact DECIMAL(4,2),
    suggested_owner VARCHAR(50),
    status       VARCHAR(10) DEFAULT 'active' CHECK (status IN ('active', 'dismissed', 'resolved')),
    dismissed_at TIMESTAMP,
    resolved_at  TIMESTAMP,
    created_by   VARCHAR(100) DEFAULT 'anomaly_scanner'
);

-- Alert thresholds: configurable per-category sensitivity
CREATE TABLE IF NOT EXISTS alert_thresholds (
    id           SERIAL PRIMARY KEY,
    category     VARCHAR(50) UNIQUE NOT NULL,
    warn_pct     DECIMAL(5,2) DEFAULT 15.0,
    critical_pct DECIMAL(5,2) DEFAULT 50.0,
    stddev_warn  DECIMAL(3,1) DEFAULT 1.5,
    stddev_crit  DECIMAL(3,1) DEFAULT 2.5,
    enabled      BOOLEAN DEFAULT true,
    updated_at   TIMESTAMP DEFAULT now()
);

-- Indexes for querying
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_category_status ON alerts(category, status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- Insert default thresholds for SeedlingLabs expense categories
INSERT INTO alert_thresholds (category) VALUES
    ('aws'), ('payroll'), ('saas'), ('marketing'),
    ('legal'), ('office'), ('contractors'), ('misc')
ON CONFLICT (category) DO NOTHING;

-- Audit log for anomaly runs (for monitoring)
CREATE TABLE IF NOT EXISTS anomaly_runs (
    id           SERIAL PRIMARY KEY,
    run_at       TIMESTAMP DEFAULT now(),
    status       VARCHAR(20),
    alerts_found INT DEFAULT 0,
    duration_ms  INT,
    error_msg    TEXT,
    version      VARCHAR(20) DEFAULT '1.0'
);

CREATE INDEX IF NOT EXISTS idx_anomaly_runs_run_at ON anomaly_runs(run_at DESC);
