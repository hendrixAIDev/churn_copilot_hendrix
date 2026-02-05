-- Migration: Add onboarding_completed column to user_preferences
-- Date: 2025-02-05
-- Description: Adds flag to track if user has completed onboarding wizard

-- Add column if it doesn't exist
ALTER TABLE user_preferences 
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;

-- Set existing users to completed (they've already used the app)
UPDATE user_preferences 
SET onboarding_completed = TRUE 
WHERE onboarding_completed IS NULL OR onboarding_completed = FALSE;
