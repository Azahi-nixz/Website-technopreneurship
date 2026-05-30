-- Migration 002: Add is_admin flag to users table
-- Adds the is_admin boolean column required for admin-only product management.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE;
