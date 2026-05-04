"""Product repository — JSON file-based storage for products and images."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from app.db import read_collection, write_collection
from app.models.product import Product, ProductImage

_COL = "products"


def _dict_to_image(d: dict) -> ProductImage:
    return ProductImage(
        id=UUID(d["id"]),
        product_id=UUID(d["product_id"]),
        image_url=d["image_url"],
        display_order=int(d["display_order"]),
    )


def _dict_to_product(d: dict) -> Product:
    images = [_dict_to_image(i) for i in d.get("images", [])]
    images.sort(key=lambda i: i.display_order)
    return Product(
        id=UUID(d["id"]),
        name=d["name"],
        description=d.get("description"),
        price=Decimal(str(d["price"])),
        is_active=bool(d.get("is_active", True)),
        created_at=datetime.fromisoformat(d["created_at"]),
        images=images,
    )


def list_active() -> List[Product]:
    products = read_collection(_COL)
    active = [_dict_to_product(p) for p in products if p.get("is_active", True)]
    active.sort(key=lambda p: p.created_at, reverse=True)
    return active


def find_by_id(product_id: UUID) -> Optional[Product]:
    """Return the product by id only if it is active."""
    products = read_collection(_COL)
    sid = str(product_id)
    for p in products:
        if p["id"] == sid and p.get("is_active", True):
            return _dict_to_product(p)
    return None


def find_by_id_any(product_id: UUID) -> Optional[Product]:
    """Return the product by id regardless of is_active status (admin use)."""
    products = read_collection(_COL)
    sid = str(product_id)
    for p in products:
        if p["id"] == sid:
            return _dict_to_product(p)
    return None


def get_images(product_id: UUID) -> List[ProductImage]:
    products = read_collection(_COL)
    sid = str(product_id)
    for p in products:
        if p["id"] == sid:
            images = [_dict_to_image(i) for i in p.get("images", [])]
            images.sort(key=lambda i: i.display_order)
            return images
    return []


# ---------------------------------------------------------------------------
# Admin helpers (used by the product management API)
# ---------------------------------------------------------------------------

def create_product(name: str, description: Optional[str], price: Decimal) -> Product:
    products = read_collection(_COL)
    product = {
        "id": str(uuid4()),
        "name": name,
        "description": description,
        "price": str(price),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "images": [],
    }
    products.append(product)
    write_collection(_COL, products)
    return _dict_to_product(product)


def update_product(product_id: UUID, **fields) -> Optional[Product]:
    products = read_collection(_COL)
    sid = str(product_id)
    for p in products:
        if p["id"] == sid:
            for k, v in fields.items():
                p[k] = str(v) if k == "price" else v
            write_collection(_COL, products)
            return _dict_to_product(p)
    return None


def delete_product(product_id: UUID) -> bool:
    products = read_collection(_COL)
    sid = str(product_id)
    new = [p for p in products if p["id"] != sid]
    if len(new) == len(products):
        return False
    write_collection(_COL, new)
    return True


def add_image(product_id: UUID, image_url: str) -> Optional[ProductImage]:
    products = read_collection(_COL)
    sid = str(product_id)
    for p in products:
        if p["id"] == sid:
            existing = p.get("images", [])
            next_order = max((i["display_order"] for i in existing), default=-1) + 1
            img = {
                "id": str(uuid4()),
                "product_id": sid,
                "image_url": image_url,
                "display_order": next_order,
            }
            existing.append(img)
            p["images"] = existing
            write_collection(_COL, products)
            return _dict_to_image(img)
    return None


def remove_image(product_id: UUID, image_id: UUID) -> bool:
    products = read_collection(_COL)
    pid = str(product_id)
    iid = str(image_id)
    for p in products:
        if p["id"] == pid:
            before = len(p.get("images", []))
            p["images"] = [i for i in p.get("images", []) if i["id"] != iid]
            if len(p["images"]) < before:
                write_collection(_COL, products)
                return True
    return False
