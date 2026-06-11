"""Cart repository — PostgreSQL or JSON file-based storage for cart items."""

from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from app.db import USE_POSTGRES
from app.models.cart import CartItem


def _row_to_cart_item(row, product=None) -> CartItem:
    if isinstance(row, dict):
        from app.repositories import product_repository
        prod = product or (product_repository.find_by_id(UUID(row["product_id"])) if row.get("product_id") else None)
        return CartItem(
            id=UUID(row["id"]),
            user_id=UUID(row["user_id"]),
            product_id=UUID(row["product_id"]),
            quantity=int(row["quantity"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            product=prod,
        )
    else:
        # pg8000 row: (id, user_id, product_id, quantity, updated_at)
        updated_at = row[4]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        return CartItem(
            id=UUID(str(row[0])),
            user_id=UUID(str(row[1])),
            product_id=UUID(str(row[2])),
            quantity=int(row[3]),
            updated_at=updated_at,
            product=product,
        )


def get_cart(user_id: UUID) -> List[CartItem]:
    if USE_POSTGRES:
        from app.db import get_connection
        from app.repositories import product_repository
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, user_id, product_id, quantity, updated_at
                FROM cart_items WHERE user_id = :user_id
                ORDER BY updated_at DESC
            """, user_id=str(user_id))
            result = []
            for row in rows:
                product = product_repository.find_by_id(UUID(str(row[2])))
                result.append(_row_to_cart_item(row, product))
            return result
    else:
        from app.db import read_collection
        from app.repositories import product_repository
        items = read_collection("cart_items")
        uid = str(user_id)
        user_items = [i for i in items if i["user_id"] == uid]
        user_items.sort(key=lambda i: i["updated_at"], reverse=True)
        return [_row_to_cart_item(i) for i in user_items]


def add_item(user_id: UUID, product_id: UUID, quantity: int) -> CartItem:
    if USE_POSTGRES:
        from app.db import get_connection
        from app.repositories import product_repository
        with get_connection() as conn:
            rows = conn.run("""
                INSERT INTO cart_items (id, user_id, product_id, quantity, updated_at)
                VALUES (:id, :user_id, :product_id, :quantity, NOW())
                ON CONFLICT (user_id, product_id)
                DO UPDATE SET quantity = cart_items.quantity + :quantity, updated_at = NOW()
                RETURNING id, user_id, product_id, quantity, updated_at
            """, id=str(uuid4()), user_id=str(user_id),
                product_id=str(product_id), quantity=quantity)
            product = product_repository.find_by_id(product_id)
            return _row_to_cart_item(rows[0], product)
    else:
        from app.db import read_collection, write_collection
        items = read_collection("cart_items")
        uid = str(user_id)
        pid = str(product_id)
        now = datetime.now(timezone.utc).isoformat()
        for item in items:
            if item["user_id"] == uid and item["product_id"] == pid:
                item["quantity"] = item["quantity"] + quantity
                item["updated_at"] = now
                write_collection("cart_items", items)
                return _row_to_cart_item(item)
        new_item = {
            "id": str(uuid4()),
            "user_id": uid,
            "product_id": pid,
            "quantity": quantity,
            "updated_at": now,
        }
        items.append(new_item)
        write_collection("cart_items", items)
        return _row_to_cart_item(new_item)


def update_item(cart_item_id: UUID, quantity: int) -> CartItem:
    if USE_POSTGRES:
        from app.db import get_connection
        from app.repositories import product_repository
        with get_connection() as conn:
            rows = conn.run("""
                UPDATE cart_items SET quantity = :quantity, updated_at = NOW()
                WHERE id = :id
                RETURNING id, user_id, product_id, quantity, updated_at
            """, quantity=quantity, id=str(cart_item_id))
            if not rows:
                raise ValueError(f"Cart item {cart_item_id} not found.")
            product = product_repository.find_by_id(UUID(str(rows[0][2])))
            return _row_to_cart_item(rows[0], product)
    else:
        from app.db import read_collection, write_collection
        items = read_collection("cart_items")
        iid = str(cart_item_id)
        for item in items:
            if item["id"] == iid:
                item["quantity"] = quantity
                item["updated_at"] = datetime.now(timezone.utc).isoformat()
                write_collection("cart_items", items)
                return _row_to_cart_item(item)
        raise ValueError(f"Cart item {cart_item_id} not found.")


def remove_item(cart_item_id: UUID) -> None:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            conn.run("DELETE FROM cart_items WHERE id = :id", id=str(cart_item_id))
    else:
        from app.db import read_collection, write_collection
        items = read_collection("cart_items")
        iid = str(cart_item_id)
        write_collection("cart_items", [i for i in items if i["id"] != iid])


def clear_cart(user_id: UUID) -> None:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            conn.run("DELETE FROM cart_items WHERE user_id = :user_id", user_id=str(user_id))
    else:
        from app.db import read_collection, write_collection
        items = read_collection("cart_items")
        uid = str(user_id)
        write_collection("cart_items", [i for i in items if i["user_id"] != uid])
