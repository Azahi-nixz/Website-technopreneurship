"""Product repository — PostgreSQL or JSON file-based storage for products."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from app.db import USE_POSTGRES
from app.models.product import Product, ProductImage


def _row_to_image(row) -> ProductImage:
    if isinstance(row, dict):
        try:
            img_id = UUID(row["id"])
        except (ValueError, AttributeError):
            img_id = uuid4()
        try:
            prod_id = UUID(row["product_id"])
        except (ValueError, AttributeError):
            prod_id = uuid4()
        return ProductImage(
            id=img_id,
            product_id=prod_id,
            image_url=row["image_url"],
            display_order=int(row["display_order"]),
        )
    else:
        # pg8000 row: (id, product_id, image_url, display_order)
        return ProductImage(
            id=UUID(str(row[0])),
            product_id=UUID(str(row[1])),
            image_url=row[2],
            display_order=int(row[3]),
        )


def _row_to_product(row, images=None) -> Product:
    if isinstance(row, dict):
        imgs = [_row_to_image(i) for i in row.get("images", [])]
        imgs.sort(key=lambda i: i.display_order)
        return Product(
            id=UUID(row["id"]),
            name=row["name"],
            description=row.get("description"),
            price=Decimal(str(row["price"])),
            is_active=bool(row.get("is_active", True)),
            created_at=datetime.fromisoformat(row["created_at"]),
            images=imgs,
        )
    else:
        # pg8000 row: (id, name, description, price, is_active, created_at)
        imgs = images or []
        imgs.sort(key=lambda i: i.display_order)
        created_at = row[5]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return Product(
            id=UUID(str(row[0])),
            name=row[1],
            description=row[2],
            price=Decimal(str(row[3])),
            is_active=bool(row[4]),
            created_at=created_at,
            images=imgs,
        )


def _fetch_images_for_products(conn, product_ids: List[str]) -> dict:
    """Fetch all images for a list of product IDs. Returns dict keyed by product_id."""
    if not product_ids:
        return {}
    placeholders = ", ".join([f":id{i}" for i in range(len(product_ids))])
    kwargs = {f"id{i}": pid for i, pid in enumerate(product_ids)}
    rows = conn.run(
        f"SELECT id, product_id, image_url, display_order FROM product_images WHERE product_id IN ({placeholders}) ORDER BY display_order",
        **kwargs
    )
    result = {}
    for r in rows:
        pid = str(r[1])
        if pid not in result:
            result[pid] = []
        result[pid].append(_row_to_image(r))
    return result


def list_active() -> List[Product]:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, name, description, price, is_active, created_at
                FROM products WHERE is_active = TRUE
                ORDER BY created_at DESC
            """)
            if not rows:
                return []
            product_ids = [str(r[0]) for r in rows]
            images_map = _fetch_images_for_products(conn, product_ids)
            return [_row_to_product(r, images_map.get(str(r[0]), [])) for r in rows]
    else:
        from app.db import read_collection
        products = read_collection("products")
        active = [_row_to_product(p) for p in products if p.get("is_active", True)]
        active.sort(key=lambda p: p.created_at, reverse=True)
        return active


def find_by_id(product_id: UUID) -> Optional[Product]:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, name, description, price, is_active, created_at
                FROM products WHERE id = :id AND is_active = TRUE
            """, id=str(product_id))
            if not rows:
                return None
            images_map = _fetch_images_for_products(conn, [str(rows[0][0])])
            return _row_to_product(rows[0], images_map.get(str(rows[0][0]), []))
    else:
        from app.db import read_collection
        products = read_collection("products")
        sid = str(product_id)
        for p in products:
            if p["id"] == sid and p.get("is_active", True):
                return _row_to_product(p)
        return None


def find_by_id_any(product_id: UUID) -> Optional[Product]:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, name, description, price, is_active, created_at
                FROM products WHERE id = :id
            """, id=str(product_id))
            if not rows:
                return None
            images_map = _fetch_images_for_products(conn, [str(rows[0][0])])
            return _row_to_product(rows[0], images_map.get(str(rows[0][0]), []))
    else:
        from app.db import read_collection
        products = read_collection("products")
        sid = str(product_id)
        for p in products:
            if p["id"] == sid:
                return _row_to_product(p)
        return None


def get_images(product_id: UUID) -> List[ProductImage]:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, product_id, image_url, display_order
                FROM product_images WHERE product_id = :id
                ORDER BY display_order
            """, id=str(product_id))
            return [_row_to_image(r) for r in rows]
    else:
        from app.db import read_collection
        products = read_collection("products")
        sid = str(product_id)
        for p in products:
            if p["id"] == sid:
                imgs = [_row_to_image(i) for i in p.get("images", [])]
                imgs.sort(key=lambda i: i.display_order)
                return imgs
        return []


def list_all() -> List[Product]:
    """Return all products including inactive (admin use)."""
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, name, description, price, is_active, created_at
                FROM products ORDER BY created_at DESC
            """)
            if not rows:
                return []
            product_ids = [str(r[0]) for r in rows]
            images_map = _fetch_images_for_products(conn, product_ids)
            return [_row_to_product(r, images_map.get(str(r[0]), [])) for r in rows]
    else:
        from app.db import read_collection
        products = read_collection("products")
        all_products = [_row_to_product(p) for p in products]
        all_products.sort(key=lambda p: p.created_at, reverse=True)
        return all_products


def create_product(name: str, description: Optional[str], price: Decimal) -> Product:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                INSERT INTO products (id, name, description, price, is_active, created_at)
                VALUES (:id, :name, :description, :price, TRUE, NOW())
                RETURNING id, name, description, price, is_active, created_at
            """, id=str(uuid4()), name=name, description=description, price=str(price))
            return _row_to_product(rows[0], [])
    else:
        from app.db import read_collection, write_collection
        products = read_collection("products")
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
        write_collection("products", products)
        return _row_to_product(product)


def update_product(product_id: UUID, **fields) -> Optional[Product]:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            if not fields:
                return find_by_id_any(product_id)
            set_clauses = []
            kwargs = {"id": str(product_id)}
            for k, v in fields.items():
                set_clauses.append(f"{k} = :{k}")
                kwargs[k] = str(v) if k == "price" else v
            sql = f"UPDATE products SET {', '.join(set_clauses)} WHERE id = :id RETURNING id, name, description, price, is_active, created_at"
            rows = conn.run(sql, **kwargs)
            if not rows:
                return None
            images_map = _fetch_images_for_products(conn, [str(rows[0][0])])
            return _row_to_product(rows[0], images_map.get(str(rows[0][0]), []))
    else:
        from app.db import read_collection, write_collection
        products = read_collection("products")
        sid = str(product_id)
        for p in products:
            if p["id"] == sid:
                for k, v in fields.items():
                    p[k] = str(v) if k == "price" else v
                write_collection("products", products)
                return _row_to_product(p)
        return None


def delete_product(product_id: UUID) -> bool:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("DELETE FROM products WHERE id = :id RETURNING id", id=str(product_id))
            return bool(rows)
    else:
        from app.db import read_collection, write_collection
        products = read_collection("products")
        sid = str(product_id)
        new = [p for p in products if p["id"] != sid]
        if len(new) == len(products):
            return False
        write_collection("products", new)
        return True


def add_image(product_id: UUID, image_url: str) -> Optional[ProductImage]:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            existing = conn.run("""
                SELECT COALESCE(MAX(display_order), -1) FROM product_images WHERE product_id = :id
            """, id=str(product_id))
            next_order = (existing[0][0] if existing else -1) + 1
            rows = conn.run("""
                INSERT INTO product_images (id, product_id, image_url, display_order)
                VALUES (:id, :product_id, :image_url, :display_order)
                RETURNING id, product_id, image_url, display_order
            """, id=str(uuid4()), product_id=str(product_id),
                image_url=image_url, display_order=next_order)
            return _row_to_image(rows[0]) if rows else None
    else:
        from app.db import read_collection, write_collection
        products = read_collection("products")
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
                write_collection("products", products)
                return _row_to_image(img)
        return None


def remove_image(product_id: UUID, image_id: UUID) -> bool:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                DELETE FROM product_images WHERE id = :id AND product_id = :product_id RETURNING id
            """, id=str(image_id), product_id=str(product_id))
            return bool(rows)
    else:
        from app.db import read_collection, write_collection
        products = read_collection("products")
        pid = str(product_id)
        iid = str(image_id)
        for p in products:
            if p["id"] == pid:
                before = len(p.get("images", []))
                p["images"] = [i for i in p.get("images", []) if i["id"] != iid]
                if len(p["images"]) < before:
                    write_collection("products", products)
                    return True
        return False
