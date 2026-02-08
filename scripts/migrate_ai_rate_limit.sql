-- Migration: Add daily tracking and token logging to AI rate limiting
-- Run this against production Supabase

-- Add day_key column to ai_extractions for daily tracking
ALTER TABLE ai_extractions 
ADD COLUMN IF NOT EXISTS day_key VARCHAR(10);

-- Create unique constraint on user_id + day_key (instead of month_key)
-- First drop the old constraint if it exists
ALTER TABLE ai_extractions DROP CONSTRAINT IF EXISTS ai_extractions_user_id_month_key_key;

-- Create new constraint on day_key
ALTER TABLE ai_extractions 
ADD CONSTRAINT ai_extractions_user_id_day_key_key UNIQUE (user_id, day_key);

-- Create index for efficient monthly queries
CREATE INDEX IF NOT EXISTS idx_ai_extractions_month 
ON ai_extractions(month_key);

-- Create token usage logging table (no PII)
CREATE TABLE IF NOT EXISTS ai_extraction_logs (
    id SERIAL PRIMARY KEY,
    extraction_id VARCHAR(8) NOT NULL,
    user_id UUID NOT NULL,
    month_key VARCHAR(7) NOT NULL,
    day_key VARCHAR(10) NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    model VARCHAR(50),
    extraction_type VARCHAR(20) DEFAULT 'url',
    success BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for analytics queries
CREATE INDEX IF NOT EXISTS idx_ai_logs_month 
ON ai_extraction_logs(month_key);

CREATE INDEX IF NOT EXISTS idx_ai_logs_user 
ON ai_extraction_logs(user_id);

-- View for usage analytics (no PII exposed)
CREATE OR REPLACE VIEW ai_usage_summary AS
SELECT 
    month_key,
    COUNT(*) as total_extractions,
    COUNT(DISTINCT user_id) as unique_users,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    ROUND(AVG(input_tokens + output_tokens)) as avg_tokens_per_extraction
FROM ai_extraction_logs
GROUP BY month_key
ORDER BY month_key DESC;
