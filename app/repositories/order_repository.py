"""Order repository — PostgreSQL or JSON file-based storage for orders."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from app.db import USE_POSTGRES
from app.models.order import Order, OrderItem


def _row_to_order_item(row) -> OrderItem:
    if isinstance(row, dict):
        return OrderItem(
            id=UUID(row["id"]),
            order_id=UUID(row["order_id"]),
            product_id=UUID(row["product_id"]),
            quantity=int(row["quantity"]),
            unit_price=Decimal(str(row["unit_price"])),
        )
    else:
        # pg8000 row: (id, order_id, product_id, quantity, unit_price)
        return OrderItem(
            id=UUID(str(row[0])),
            order_id=UUID(str(row[1])),
            product_id=UUID(str(row[2])),
            quantity=int(row[3]),
            unit_price=Decimal(str(row[4])),
        )


def _row_to_order(row, items=None) -> Order:
    if isinstance(row, dict):
        order_items = [_row_to_order_item(i) for i in row.get("items", [])]
        return Order(
            id=UUID(row["id"]),
            user_id=UUID(row["user_id"]),
            total_amount=Decimal(str(row["total_amount"])),
            status=row.get("status", "pending"),
            created_at=datetime.fromisoformat(row["created_at"]),
            items=order_items,
        )
    else:
        # pg8000 row: (id, user_id, total_amount, status, created_at)
        created_at = row[4]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        return Order(
            id=UUID(str(row[0])),
            user_id=UUID(str(row[1])),
            total_amount=Decimal(str(row[2])),
            status=row[3],
            created_at=created_at,
            items=items or [],
        )


def _fetch_items_for_orders(conn, order_ids: List[str]) -> dict:
    if not order_ids:
        return {}
    placeholders = ", ".join([f":id{i}" for i in range(len(order_ids))])
    kwargs = {f"id{i}": oid for i, oid in enumerate(order_ids)}
    rows = conn.run(
        f"SELECT id, order_id, product_id, quantity, unit_price FROM order_items WHERE order_id IN ({placeholders})",
        **kwargs
    )
    result = {}
    for r in rows:
        oid = str(r[1])
        if oid not in result:
            result[oid] = []
        result[oid].append(_row_to_order_item(r))
    return result


def create_order(user_id: UUID, items: List[dict], total_amount: Decimal) -> Order:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            order_id = str(uuid4())
            rows = conn.run("""
                INSERT INTO orders (id, user_id, total_amount, status, created_at)
                VALUES (:id, :user_id, :total_amount, 'pending', NOW())
                RETURNING id, user_id, total_amount, status, created_at
            """, id=order_id, user_id=str(user_id), total_amount=str(total_amount))

            order_items = []
            for item in items:
                item_id = str(uuid4())
                conn.run("""
                    INSERT INTO order_items (id, order_id, product_id, quantity, unit_price)
                    VALUES (:id, :order_id, :product_id, :quantity, :unit_price)
                """, id=item_id, order_id=order_id,
                    product_id=str(item["product_id"]),
                    quantity=item["quantity"],
                    unit_price=str(item["unit_price"]))
                order_items.append(OrderItem(
                    id=UUID(item_id),
                    order_id=UUID(order_id),
                    product_id=UUID(str(item["product_id"])),
                    quantity=item["quantity"],
                    unit_price=Decimal(str(item["unit_price"])),
                ))
            return _row_to_order(rows[0], order_items)
    else:
        from app.db import read_collection, write_collection
        orders = read_collection("orders")
        order_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        order_items_data = []
        for item in items:
            order_items_data.append({
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
            "items": order_items_data,
        }
        orders.append(order)
        write_collection("orders", orders)
        return _row_to_order(order)


def find_by_id(order_id: UUID) -> Optional[Order]:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, user_id, total_amount, status, created_at
                FROM orders WHERE id = :id
            """, id=str(order_id))
            if not rows:
                return None
            items_map = _fetch_items_for_orders(conn, [str(rows[0][0])])
            return _row_to_order(rows[0], items_map.get(str(rows[0][0]), []))
    else:
        from app.db import read_collection
        orders = read_collection("orders")
        sid = str(order_id)
        for o in orders:
            if o["id"] == sid:
                return _row_to_order(o)
        return None


def list_by_user(user_id: UUID) -> List[Order]:
    if USE_POSTGRES:
        from app.db import get_connection
        with get_connection() as conn:
            rows = conn.run("""
                SELECT id, user_id, total_amount, status, created_at
                FROM orders WHERE user_id = :user_id
                ORDER BY created_at DESC
            """, user_id=str(user_id))
            if not rows:
                return []
            order_ids = [str(r[0]) for r in rows]
            items_map = _fetch_items_for_orders(conn, order_ids)
            return [_row_to_order(r, items_map.get(str(r[0]), [])) for r in rows]
    else:
        from app.db import read_collection
        orders = read_collection("orders")
        uid = str(user_id)
        user_orders = [_row_to_order(o) for o in orders if o["user_id"] == uid]
        user_orders.sort(key=lambda o: o.created_at, reverse=True)
        return user_orders
