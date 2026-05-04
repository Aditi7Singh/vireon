-- Migration: Add missing 'settings' column to companies table
-- Run this when PostgreSQL is accessible
-- Usage: psql -U vireon -d vireon -h localhost -p 5433 -f add_settings_column.sql

BEGIN;

-- Check if column exists before adding
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'companies' AND column_name = 'settings'
    ) THEN
        ALTER TABLE companies ADD COLUMN settings JSONB NULL DEFAULT '{}';
        RAISE NOTICE 'Added settings column to companies table';
    ELSE
        RAISE NOTICE 'settings column already exists in companies table';
    END IF;
END $$;

COMMIT;
