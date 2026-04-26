-- Finance Agent Database Schema
-- Based on Merge.dev Accounting API Architecture
-- PostgreSQL Schema for Financial Data

-- ============================================================================
-- CORE ENTITIES
-- ============================================================================

-- Companies Table (Multi-tenant support)
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    stage VARCHAR(50), -- seed, series_a, series_b, growth
    initial_cash DECIMAL(15, 2) NOT NULL,
    founding_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts (Chart of Accounts)
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255), -- Merge.dev remote_id
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    classification VARCHAR(50), -- asset, liability, equity, revenue, expense
    type VARCHAR(50), -- cash, bank, accounts_receivable, accounts_payable, etc.
    status VARCHAR(20) DEFAULT 'active', -- active, archived
    current_balance DECIMAL(15, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    remote_created_at TIMESTAMP,
    remote_modified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TRANSACTIONS & PAYMENTS
-- ============================================================================

-- Invoices (AR - Accounts Receivable)
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    invoice_number VARCHAR(100) UNIQUE NOT NULL,
    contact_id UUID, -- References contacts/customers
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    payment_date DATE,
    status VARCHAR(50), -- draft, submitted, paid, void, overdue
    type VARCHAR(50), -- standard, recurring, credit_note
    sub_total DECIMAL(15, 2) NOT NULL,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    total_amount DECIMAL(15, 2) NOT NULL,
    amount_paid DECIMAL(15, 2) DEFAULT 0,
    amount_due DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    memo TEXT,
    remote_created_at TIMESTAMP,
    remote_modified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Invoice Line Items
CREATE TABLE invoice_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    quantity DECIMAL(10, 2) DEFAULT 1,
    unit_price DECIMAL(15, 2) NOT NULL,
    total_amount DECIMAL(15, 2) NOT NULL,
    account_id UUID REFERENCES accounts(id),
    item_id UUID, -- References items/products
    tracking_category_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expenses
CREATE TABLE expenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    account_id UUID REFERENCES accounts(id),
    contact_id UUID, -- Vendor
    total_amount DECIMAL(15, 2) NOT NULL,
    sub_total DECIMAL(15, 2),
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'USD',
    exchange_rate DECIMAL(10, 6) DEFAULT 1.0,
    category VARCHAR(100), -- Software, Payroll, Cloud, Marketing, etc.
    subcategory VARCHAR(100),
    payment_method VARCHAR(50), -- credit_card, bank_transfer, check, cash
    memo TEXT,
    receipt_url TEXT,
    is_billable BOOLEAN DEFAULT FALSE,
    remote_created_at TIMESTAMP,
    remote_modified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Expense Line Items
CREATE TABLE expense_line_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    expense_id UUID REFERENCES expenses(id) ON DELETE CASCADE,
    description TEXT,
    amount DECIMAL(15, 2) NOT NULL,
    account_id UUID REFERENCES accounts(id),
    tracking_category_id UUID,
    tax_amount DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payments (Cash movements)
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    contact_id UUID,
    account_id UUID REFERENCES accounts(id), -- Bank/Cash account
    total_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    exchange_rate DECIMAL(10, 6) DEFAULT 1.0,
    type VARCHAR(50), -- payment_received, payment_sent, transfer
    payment_method VARCHAR(50),
    reference VARCHAR(255),
    memo TEXT,
    remote_created_at TIMESTAMP,
    remote_modified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONTACTS (Customers & Vendors)
-- ============================================================================

CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- customer, vendor, employee, other
    email VARCHAR(255),
    phone VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    payment_terms VARCHAR(50), -- net_30, net_60, due_on_receipt, etc.
    currency VARCHAR(3) DEFAULT 'USD',
    billing_address JSONB,
    shipping_address JSONB,
    tax_number VARCHAR(100),
    remote_created_at TIMESTAMP,
    remote_modified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- TRACKING & CATEGORIZATION
-- ============================================================================

-- Tracking Categories (Departments, Projects, Locations, etc.)
CREATE TABLE tracking_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- department, project, location, cost_center
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Items/Products/Services
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50), -- service, inventory, non_inventory
    status VARCHAR(20) DEFAULT 'active',
    unit_price DECIMAL(15, 2),
    purchase_price DECIMAL(15, 2),
    sales_account_id UUID REFERENCES accounts(id),
    expense_account_id UUID REFERENCES accounts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PAYROLL & EMPLOYEES
-- ============================================================================

CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    employment_status VARCHAR(50), -- active, terminated, on_leave
    employment_type VARCHAR(50), -- full_time, part_time, contractor
    department VARCHAR(100),
    job_title VARCHAR(100),
    hire_date DATE,
    termination_date DATE,
    salary DECIMAL(15, 2),
    pay_frequency VARCHAR(50), -- monthly, semi_monthly, biweekly, weekly
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payroll_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    remote_id VARCHAR(255),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    run_date DATE NOT NULL,
    pay_period_start DATE NOT NULL,
    pay_period_end DATE NOT NULL,
    check_date DATE NOT NULL,
    status VARCHAR(50), -- draft, approved, paid, void
    total_gross_pay DECIMAL(15, 2) NOT NULL,
    total_employer_taxes DECIMAL(15, 2) DEFAULT 0,
    total_employee_taxes DECIMAL(15, 2) DEFAULT 0,
    total_benefits DECIMAL(15, 2) DEFAULT 0,
    total_deductions DECIMAL(15, 2) DEFAULT 0,
    total_net_pay DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payroll_run_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payroll_run_id UUID REFERENCES payroll_runs(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id),
    gross_pay DECIMAL(15, 2) NOT NULL,
    employer_taxes DECIMAL(15, 2) DEFAULT 0,
    employee_taxes DECIMAL(15, 2) DEFAULT 0,
    benefits DECIMAL(15, 2) DEFAULT 0,
    deductions DECIMAL(15, 2) DEFAULT 0,
    net_pay DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CLOUD INFRASTRUCTURE COSTS
-- ============================================================================

CREATE TABLE cloud_costs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    provider VARCHAR(50), -- aws, gcp, azure
    service VARCHAR(100), -- ec2, s3, rds, compute_engine, etc.
    billing_date DATE NOT NULL,
    region VARCHAR(50),
    resource_id VARCHAR(255),
    resource_name VARCHAR(255),
    usage_quantity DECIMAL(15, 4),
    usage_unit VARCHAR(50), -- hours, GB, requests
    cost DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    tags JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FINANCIAL METRICS & AGGREGATIONS
-- ============================================================================

CREATE TABLE monthly_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    metric_month DATE NOT NULL, -- First day of month
    
    -- Cash metrics
    starting_cash DECIMAL(15, 2) NOT NULL,
    ending_cash DECIMAL(15, 2) NOT NULL,
    cash_inflow DECIMAL(15, 2) DEFAULT 0,
    cash_outflow DECIMAL(15, 2) DEFAULT 0,
    net_cash_flow DECIMAL(15, 2) DEFAULT 0,
    
    -- Revenue metrics
    total_revenue DECIMAL(15, 2) DEFAULT 0,
    recurring_revenue DECIMAL(15, 2) DEFAULT 0, -- MRR
    one_time_revenue DECIMAL(15, 2) DEFAULT 0,
    
    -- Expense metrics
    total_expenses DECIMAL(15, 2) DEFAULT 0,
    payroll_expenses DECIMAL(15, 2) DEFAULT 0,
    cloud_expenses DECIMAL(15, 2) DEFAULT 0,
    marketing_expenses DECIMAL(15, 2) DEFAULT 0,
    sales_expenses DECIMAL(15, 2) DEFAULT 0,
    rnd_expenses DECIMAL(15, 2) DEFAULT 0,
    operations_expenses DECIMAL(15, 2) DEFAULT 0,
    
    -- Calculated metrics
    burn_rate DECIMAL(15, 2) DEFAULT 0,
    runway_months DECIMAL(5, 2) DEFAULT 0,
    gross_margin DECIMAL(5, 2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(company_id, metric_month)
);

-- ============================================================================
-- ANOMALY DETECTION
-- ============================================================================

CREATE TABLE anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    anomaly_date DATE NOT NULL,
    severity VARCHAR(20), -- critical, warning, info
    type VARCHAR(50), -- expense_spike, duplicate_payment, revenue_drop, etc.
    category VARCHAR(100), -- expense category or revenue stream
    description TEXT NOT NULL,
    
    -- Metrics
    expected_value DECIMAL(15, 2),
    actual_value DECIMAL(15, 2),
    variance_percent DECIMAL(5, 2),
    variance_amount DECIMAL(15, 2),
    
    -- Context
    baseline_period VARCHAR(50), -- 90_day_average, 6_month_trend, etc.
    affected_entity_type VARCHAR(50), -- expense, invoice, vendor, etc.
    affected_entity_id UUID,
    
    -- Status
    status VARCHAR(20) DEFAULT 'open', -- open, investigating, resolved, false_positive
    investigated_by VARCHAR(255),
    resolution_notes TEXT,
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Company-based queries
CREATE INDEX idx_accounts_company ON accounts(company_id);
CREATE INDEX idx_invoices_company ON invoices(company_id);
CREATE INDEX idx_expenses_company ON expenses(company_id);
CREATE INDEX idx_payments_company ON payments(company_id);
CREATE INDEX idx_contacts_company ON contacts(company_id);
CREATE INDEX idx_employees_company ON employees(company_id);
CREATE INDEX idx_cloud_costs_company ON cloud_costs(company_id);

-- Date-based queries
CREATE INDEX idx_invoices_issue_date ON invoices(issue_date);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_expenses_transaction_date ON expenses(transaction_date);
CREATE INDEX idx_payments_transaction_date ON payments(transaction_date);
CREATE INDEX idx_cloud_costs_billing_date ON cloud_costs(billing_date);
CREATE INDEX idx_monthly_metrics_month ON monthly_metrics(metric_month);
CREATE INDEX idx_anomalies_date ON anomalies(anomaly_date);

-- Status and category queries
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_anomalies_status ON anomalies(status);
CREATE INDEX idx_anomalies_severity ON anomalies(severity);

-- Composite indexes for common queries
CREATE INDEX idx_expenses_company_date ON expenses(company_id, transaction_date);
CREATE INDEX idx_invoices_company_status ON invoices(company_id, status);
CREATE INDEX idx_monthly_metrics_company_month ON monthly_metrics(company_id, metric_month);

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Current cash position
CREATE VIEW v_current_cash_position AS
SELECT 
    c.id as company_id,
    c.name as company_name,
    COALESCE(SUM(a.current_balance), 0) as total_cash
FROM companies c
LEFT JOIN accounts a ON a.company_id = c.id AND a.type IN ('cash', 'bank') AND a.status = 'active'
GROUP BY c.id, c.name;

-- Monthly burn rate (last 3 months)
CREATE VIEW v_recent_burn_rate AS
SELECT 
    company_id,
    AVG(burn_rate) as avg_burn_rate,
    AVG(total_expenses) as avg_monthly_expenses,
    AVG(total_revenue) as avg_monthly_revenue
FROM monthly_metrics
WHERE metric_month >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY company_id;

-- AR Aging
CREATE VIEW v_ar_aging AS
SELECT 
    i.company_id,
    i.contact_id,
    c.name as customer_name,
    COUNT(*) as invoice_count,
    SUM(i.amount_due) as total_outstanding,
    SUM(CASE WHEN i.due_date >= CURRENT_DATE THEN i.amount_due ELSE 0 END) as current,
    SUM(CASE WHEN i.due_date < CURRENT_DATE AND i.due_date >= CURRENT_DATE - INTERVAL '30 days' THEN i.amount_due ELSE 0 END) as days_1_30,
    SUM(CASE WHEN i.due_date < CURRENT_DATE - INTERVAL '30 days' AND i.due_date >= CURRENT_DATE - INTERVAL '60 days' THEN i.amount_due ELSE 0 END) as days_31_60,
    SUM(CASE WHEN i.due_date < CURRENT_DATE - INTERVAL '60 days' THEN i.amount_due ELSE 0 END) as over_60
FROM invoices i
LEFT JOIN contacts c ON c.id = i.contact_id
WHERE i.status IN ('submitted', 'overdue') AND i.amount_due > 0
GROUP BY i.company_id, i.contact_id, c.name;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Update account balance trigger function
CREATE OR REPLACE FUNCTION update_account_balance()
RETURNS TRIGGER AS $$
BEGIN
    -- This would be called by transaction triggers to update account balances
    -- Implementation depends on double-entry bookkeeping rules
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Calculate runway function
CREATE OR REPLACE FUNCTION calculate_runway(p_company_id UUID)
RETURNS TABLE(
    current_cash DECIMAL,
    monthly_burn DECIMAL,
    runway_months DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cash.total_cash,
        burn.avg_burn_rate,
        CASE 
            WHEN burn.avg_burn_rate > 0 THEN cash.total_cash / burn.avg_burn_rate
            ELSE 999.99
        END as runway
    FROM v_current_cash_position cash
    JOIN v_recent_burn_rate burn ON burn.company_id = cash.company_id
    WHERE cash.company_id = p_company_id;
END;
$$ LANGUAGE plpgsql;
