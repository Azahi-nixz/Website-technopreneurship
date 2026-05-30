from dataclasses import dataclass
from datetime import datetime


@dataclass
class ContentConfig:
    site_title: str
    brand_name: str
    hero_headline: str
    hero_subheadline: str
    nav_home_label: str
    nav_products_label: str
    nav_cart_label: str
    nav_orders_label: str
    footer_tagline: str
    footer_copyright: str
    section_heading: str
    section_subheading: str
    cta_shop_now: str
    cta_view_cart: str
    cta_sign_in: str
    empty_cart_message: str
    empty_orders_message: str
    updated_at: datetime
