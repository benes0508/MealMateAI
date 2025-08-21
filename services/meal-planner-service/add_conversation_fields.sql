-- Migration script to add conversation fields to meal_plans table
-- Run this script in your PostgreSQL database to add the new conversation fields

ALTER TABLE meal_plans 
ADD COLUMN IF NOT EXISTS conversation_data TEXT,
ADD COLUMN IF NOT EXISTS conversation_title VARCHAR(500),
ADD COLUMN IF NOT EXISTS original_prompt TEXT;

-- Add comments for documentation
COMMENT ON COLUMN meal_plans.conversation_data IS 'JSON string containing full chat history and context';
COMMENT ON COLUMN meal_plans.conversation_title IS 'Auto-generated descriptive title for the conversation';
COMMENT ON COLUMN meal_plans.original_prompt IS 'User''s initial request that started the meal plan creation';

-- Optional: Create index on conversation_title for searching
CREATE INDEX IF NOT EXISTS idx_meal_plans_conversation_title ON meal_plans(conversation_title);

-- Verify the changes
\d meal_plans;