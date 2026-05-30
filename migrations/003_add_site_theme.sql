-- Migration 003: Add site_theme singleton table
-- Stores the active font and color palette configuration for the site.

CREATE TABLE IF NOT EXISTS site_theme (
    id               INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    accent_color     VARCHAR(10)  NOT NULL DEFAULT '#D4AF37',
    background_color VARCHAR(10)  NOT NULL DEFAULT '#0A0E1A',
    font_family      VARCHAR(100) NOT NULL DEFAULT 'Inter',
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Seed the default row if it doesn't exist
INSERT INTO site_theme (id, accent_color, background_color, font_family)
VALUES (1, '#D4AF37', '#0A0E1A', 'Inter')
ON CONFLICT (id) DO NOTHING;
