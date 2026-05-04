"""Cart repository — JSON file-based storage for cart items."""

from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

from app.db import read_collection, write_collection
from app.models.cart import CartItem
from app.repositories import product_repository

_COL = "cart_items"


def _dict_to_cart_item(d: dict) -> CartItem:
    product = None
    if d.get("product_id"):
        product = product_repository.find_by_id(UUID(d["product_id"]))
    return CartItem(
        id=UUID(d["id"]),
        user_id=UUID(d["user_id"]),
        product_id=UUID(d["product_id"]),
        quantity=int(d["quantity"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
        product=product,
    )


def get_cart(user_id: UUID) -> List[CartItem]:
    items = read_collection(_COL)
    uid = str(user_id)
    user_items = [i for i in items if i["user_id"] == uid]
    user_items.sort(key=lambda i: i["updated_at"], reverse=True)
    return [_dict_to_cart_item(i) for i in user_items]


def add_item(user_id: UUID, product_id: UUID, quantity: int) -> CartItem:
    items = read_collection(_COL)
    uid = str(user_id)
    pid = str(product_id)
    now = datetime.now(timezone.utc).isoformat()

    for item in items:
        if item["user_id"] == uid and item["product_id"] == pid:
            item["quantity"] = item["quantity"] + quantity
            item["updated_at"] = now
            write_collection(_COL, items)
            return _dict_to_cart_item(item)

    new_item = {
        "id": str(uuid4()),
        "user_id": uid,
        "product_id": pid,
        "quantity": quantity,
        "updated_at": now,
    }
    items.append(new_item)
    write_collection(_COL, items)
    return _dict_to_cart_item(new_item)


def update_item(cart_item_id: UUID, quantity: int) -> CartItem:
    items = read_collection(_COL)
    iid = str(cart_item_id)
    for item in items:
        if item["id"] == iid:
            item["quantity"] = quantity
            item["updated_at"] = datetime.now(timezone.utc).isoformat()
            write_collection(_COL, items)
            return _dict_to_cart_item(item)
    raise ValueError(f"Cart item {cart_item_id} not found.")


def remove_item(cart_item_id: UUID) -> None:
    items = read_collection(_COL)
    iid = str(cart_item_id)
    write_collection(_COL, [i for i in items if i["id"] != iid])


def clear_cart(user_id: UUID) -> None:
    items = read_collection(_COL)
    uid = str(user_id)
    write_collection(_COL, [i for i in items if i["user_id"] != uid])
