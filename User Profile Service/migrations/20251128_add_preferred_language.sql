-- Migration: add preferred_language column to user_profiles
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS preferred_language VARCHAR(8);
UPDATE user_profiles SET preferred_language='en' WHERE preferred_language IS NULL;
ALTER TABLE user_profiles ALTER COLUMN preferred_language SET NOT NULL;