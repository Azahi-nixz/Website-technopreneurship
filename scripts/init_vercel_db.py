"""Initialize Vercel Postgres database with schema and seed data.

Run this once after creating the Vercel Postgres database:
    python scripts/init_vercel_db.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import psycopg2

def init_database():
    """Create tables and seed initial data."""
    
    postgres_url = os.environ.get("POSTGRES_URL")
    if not postgres_url:
        print("❌ POSTGRES_URL not set. Run this after creating Vercel Postgres database.")
        sys.exit(1)
    
    print(f"✓ Connecting to database...")
    conn = psycopg2.connect(postgres_url)
    cur = conn.cursor()
    
    try:
        # Read and execute migration files
        migrations_dir = Path(__file__).parent.parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        for migration_file in migration_files:
            print(f"✓ Running {migration_file.name}...")
            sql = migration_file.read_text()
            cur.execute(sql)
        
        conn.commit()
        print("✓ Database schema created successfully!")
        
        # Seed products from data/products.json
        print("✓ Seeding products...")
        products_file = Path(__file__).parent.parent / "data" / "products.json"
        if products_file.exists():
            import json
            products = json.load(products_file)
            
            for p in products:
                cur.execute("""
                    INSERT INTO products (id, name, description, price, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, (
                    p["id"], p["name"], p.get("description"),
                    p["price"], p.get("is_active", True),
                    p.get("created_at")
                ))
                
                # Insert images
                for img in p.get("images", []):
                    cur.execute("""
                        INSERT INTO product_images (id, product_id, image_url, display_order)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        img["id"], img["product_id"],
                        img["image_url"], img["display_order"]
                    ))
            
            conn.commit()
            print(f"✓ Seeded {len(products)} products!")
        
        # Seed theme
        print("✓ Seeding theme...")
        theme_file = Path(__file__).parent.parent / "data" / "theme.json"
        if theme_file.exists():
            import json
            themes = json.load(theme_file)
            if themes:
                t = themes[0]
                cur.execute("""
                    INSERT INTO site_theme (accent_color, background_color, font_family, updated_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    t.get("accent_color"), t.get("background_color"),
                    t.get("font_family"), t.get("updated_at")
                ))
                conn.commit()
                print("✓ Theme seeded!")
        
        # Seed content
        print("✓ Seeding content...")
        content_file = Path(__file__).parent.parent / "data" / "content.json"
        if content_file.exists():
            import json
            contents = json.load(content_file)
            if contents:
                c = contents[0]
                cur.execute("""
                    INSERT INTO site_content (
                        site_title, brand_name, hero_headline, hero_subheadline,
                        nav_home_label, nav_products_label, nav_cart_label, nav_orders_label,
                        footer_tagline, footer_copyright, section_heading, section_subheadline,
                        cta_shop_now, cta_view_cart, cta_sign_in,
                        empty_cart_message, empty_orders_message, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    c.get("site_title"), c.get("brand_name"),
                    c.get("hero_headline"), c.get("hero_subheadline"),
                    c.get("nav_home_label"), c.get("nav_products_label"),
                    c.get("nav_cart_label"), c.get("nav_orders_label"),
                    c.get("footer_tagline"), c.get("footer_copyright"),
                    c.get("section_heading"), c.get("section_subheadline"),
                    c.get("cta_shop_now"), c.get("cta_view_cart"), c.get("cta_sign_in"),
                    c.get("empty_cart_message"), c.get("empty_orders_message"),
                    c.get("updated_at")
                ))
                conn.commit()
                print("✓ Content seeded!")
        
        print("\n✅ Database initialization complete!")
        print("You can now deploy to Vercel.")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    init_database()
