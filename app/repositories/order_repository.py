"""Order repository — JSON file-based storage for orders and order items."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from app.db import read_collection, write_collection
from app.models.order import Order, OrderItem

_COL = "orders"


def _dict_to_order_item(d: dict) -> OrderItem:
    return OrderItem(
        id=UUID(d["id"]),
        order_id=UUID(d["order_id"]),
        product_id=UUID(d["product_id"]),
        quantity=int(d["quantity"]),
        unit_price=Decimal(str(d["unit_price"])),
    )


def _dict_to_order(d: dict) -> Order:
    items = [_dict_to_order_item(i) for i in d.get("items", [])]
    return Order(
        id=UUID(d["id"]),
        user_id=UUID(d["user_id"]),
        total_amount=Decimal(str(d["total_amount"])),
        status=d.get("status", "pending"),
        created_at=datetime.fromisoformat(d["created_at"]),
        items=items,
    )


def create_order(user_id: UUID, items: List[dict], total_amount: Decimal) -> Order:
    orders = read_collection(_COL)
    order_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    order_items = []
    for item in items:
        order_items.append({
            "id": str(uuid4()),
            "order_id": order_id,
            "product_id": str(item["product_id"]),
            "quantity": item["quantity"],
            "unit_price": str(item["unit_price"]),
        })

    order = {
        "id": order_id,
        "user_id": str(user_id),
        "total_amount": str(total_amount),
        "status": "pending",
        "created_at": now,
        "items": order_items,
    }
    orders.append(order)
    write_collection(_COL, orders)
    return _dict_to_order(order)


def find_by_id(order_id: UUID) -> Optional[Order]:
    orders = read_collection(_COL)
    sid = str(order_id)
    for o in orders:
        if o["id"] == sid:
            return _dict_to_order(o)
    return None


def list_by_user(user_id: UUID) -> List[Order]:
    orders = read_collection(_COL)
    uid = str(user_id)
    user_orders = [_dict_to_order(o) for o in orders if o["user_id"] == uid]
    user_orders.sort(key=lambda o: o.created_at, reverse=True)
    return user_orders
