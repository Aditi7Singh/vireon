-- Alerts Table Migration
-- ====================
-- Creates the alerts table for anomaly detection

-- Main alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Alert identification
    severity VARCHAR(10) NOT NULL,           -- critical / warning / info
    alert_type VARCHAR(30) NOT NULL,        -- spike / trend / duplicate / vendor / timing
    
    -- Category and amounts
    category VARCHAR(50),                    -- aws / payroll / saas / marketing / etc.
    amount DECIMAL(12, 2),                 -- actual amount that triggered alert
    baseline DECIMAL(12, 2),                -- 90-day average for this category
    delta_pct DECIMAL(6, 2),               -- % above baseline
    
    -- Period
    period_start DATE,
    period_end DATE,
    
    -- Description and impact
    description TEXT,                       -- human-readable: "AWS $18,245 vs expected $12,100"
    runway_impact DECIMAL(4, 2),           -- months of runway impact if sustained
    
    -- Ownership
    suggested_owner VARCHAR(50),            -- CTO / CFO / CEO
    
    -- Status tracking
    status VARCHAR(10) DEFAULT 'active',   -- active / dismissed / resolved
    dismissed_at TIMESTAMP,
    resolved_at TIMESTAMP,
    dismissed_by VARCHAR(100),
    resolution_notes TEXT
);

-- Alert thresholds configuration table
CREATE TABLE IF NOT EXISTS alert_thresholds (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) UNIQUE NOT NULL,
    
    -- Threshold configuration
    warn_pct DECIMAL(5, 2) DEFAULT 15.0,   -- % above baseline for warning
    critical_pct DECIMAL(5, 2) DEFAULT 50.0, -- % above baseline for critical
    stddev_warn DECIMAL(3, 1) DEFAULT 1.5,   -- std deviations for warning
    stddev_crit DECIMAL(3, 1) DEFAULT 2.5,   -- std deviations for critical
    
    -- Control
    enabled BOOLEAN DEFAULT true,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default thresholds for common expense categories
INSERT INTO alert_thresholds (category) VALUES
    ('aws'),
    ('payroll'),
    ('saas'),
    ('marketing'),
    ('legal'),
    ('office'),
    ('contractors'),
    ('misc')
ON CONFLICT (category) DO NOTHING;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_category ON alerts(category);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_company ON alerts(company_id);

-- Comments
COMMENT ON TABLE alerts IS 'Financial anomaly alerts detected by the scanner';
COMMENT ON TABLE alert_thresholds IS 'Configurable thresholds per expense category';
