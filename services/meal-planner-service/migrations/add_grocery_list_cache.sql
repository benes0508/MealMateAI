-- Migration: Add grocery list caching columns to meal_plans table
-- This allows grocery lists to be saved and automatically invalidated when meal plans change

ALTER TABLE meal_plans 
ADD COLUMN grocery_list TEXT,
ADD COLUMN grocery_list_generated_at TIMESTAMP;

-- Add index for faster lookups on generated_at for potential cleanup operations
CREATE INDEX idx_meal_plans_grocery_list_generated_at ON meal_plans(grocery_list_generated_at);