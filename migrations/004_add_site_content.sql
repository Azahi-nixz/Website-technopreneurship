-- Migration 004: Add site_content singleton table
-- Stores all editable text content for the site.

CREATE TABLE IF NOT EXISTS site_content (
    id                    INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    site_title            VARCHAR(255) NOT NULL DEFAULT 'LUXE STORE',
    brand_name            VARCHAR(255) NOT NULL DEFAULT 'Luxe Store',
    hero_headline         TEXT         NOT NULL DEFAULT 'Discover Luxury Redefined',
    hero_subheadline      TEXT         NOT NULL DEFAULT 'Curated premium products crafted for those who appreciate the finest things in life.',
    nav_home_label        VARCHAR(100) NOT NULL DEFAULT 'Home',
    nav_products_label    VARCHAR(100) NOT NULL DEFAULT 'Products',
    nav_cart_label        VARCHAR(100) NOT NULL DEFAULT 'Cart',
    nav_orders_label      VARCHAR(100) NOT NULL DEFAULT 'Orders',
    footer_tagline        TEXT         NOT NULL DEFAULT 'Premium products for discerning customers. Quality and elegance in every item.',
    footer_copyright      VARCHAR(255) NOT NULL DEFAULT '© 2024 LUXE STORE. All rights reserved.',
    section_heading       VARCHAR(255) NOT NULL DEFAULT 'Our Collection',
    section_subheading    VARCHAR(255) NOT NULL DEFAULT 'Handpicked premium items',
    cta_shop_now          VARCHAR(100) NOT NULL DEFAULT 'Shop Now',
    cta_view_cart         VARCHAR(100) NOT NULL DEFAULT 'View Cart',
    cta_sign_in           VARCHAR(100) NOT NULL DEFAULT 'Sign In',
    empty_cart_message    TEXT         NOT NULL DEFAULT 'Your cart is empty.',
    empty_orders_message  TEXT         NOT NULL DEFAULT 'No orders yet.',
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Seed the default row if it doesn't exist
INSERT INTO site_content (id) VALUES (1) ON CONFLICT (id) DO NOTHING;
