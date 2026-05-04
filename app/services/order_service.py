"""Order service — business logic layer for cart and order operations.

Delegates all database access to the cart_repository, order_repository, and
product_repository modules.  Raises domain-level exceptions so that route
handlers can map them to HTTP responses.

Requirements: 5.2, 5.3, 6.1, 6.3, 6.4, 7.1, 7.3
"""

from decimal import Decimal
from typing import List
from uuid import UUID

from app.models.cart import CartItem
from app.models.order import Order
from app.repositories import cart_repository, order_repository, product_repository
from app.services.product_service import NotFoundError


def get_cart(user_id: UUID) -> List[CartItem]:
    """Return the user's cart items with products joined.

    Delegates to cart_repository.get_cart().

    Args:
        user_id: The UUID of the authenticated user.

    Returns:
        A list of CartItem instances, each with the ``product`` field
        populated.  Returns an empty list when the cart is empty.
    """
    return cart_repository.get_cart(user_id)


def add_to_cart(user_id: UUID, product_id: UUID, quantity: int = 1) -> CartItem:
    """Add a product to the cart (upsert).

    Verifies the product exists and is active before inserting.  If a cart
    item for the same (user_id, product_id) pair already exists, the
    quantity is incremented (Requirement 6.3).

    Args:
        user_id:    The UUID of the authenticated user.
        product_id: The UUID of the product to add.
        quantity:   Number of units to add (must be ≥ 1).

    Returns:
        The CartItem as it exists in the database after the upsert.

    Raises:
        NotFoundError: If no active product with the given id exists.
    """
    product = product_repository.find_by_id(product_id)
    if product is None:
        raise NotFoundError("Product not found.")
    return cart_repository.add_item(user_id, product_id, quantity)


def update_cart_item(user_id: UUID, cart_item_id: UUID, quantity: int) -> CartItem:
    """Update the quantity of a cart item.

    Delegates to cart_repository.update_item().

    Args:
        user_id:      The UUID of the authenticated user (used for ownership
                      checks at the route layer).
        cart_item_id: The UUID primary key of the cart item to update.
        quantity:     The new quantity value (must be ≥ 1).

    Returns:
        The updated CartItem with the ``product`` field populated.

    Raises:
        ValueError: If no cart item with the given id exists.
    """
    return cart_repository.update_item(cart_item_id, quantity)


def remove_from_cart(user_id: UUID, cart_item_id: UUID) -> None:
    """Remove a cart item.

    Delegates to cart_repository.remove_item() (Requirement 6.4).

    Args:
        user_id:      The UUID of the authenticated user (used for ownership
                      checks at the route layer).
        cart_item_id: The UUID primary key of the cart item to remove.
    """
    cart_repository.remove_item(cart_item_id)


def place_order(user_id: UUID) -> Order:
    """Create an order from the user's current cart.

    - Snapshots unit prices at the time of order creation so future price
      changes do not affect historical orders (Requirement 7.1).
    - Calculates total_amount = Σ(item.product.price × item.quantity).
    - Calls order_repository.create_order() with the items list.
    - Clears the cart atomically after successful order creation.

    Args:
        user_id: The UUID of the authenticated user placing the order.

    Returns:
        The newly created Order with its ``items`` list populated.

    Raises:
        ValueError: If the user's cart is empty.
    """
    cart_items = cart_repository.get_cart(user_id)
    if not cart_items:
        raise ValueError("Cannot place order: cart is empty.")

    items = []
    total = Decimal("0")
    for ci in cart_items:
        unit_price = ci.product.price
        items.append({
            "product_id": ci.product_id,
            "quantity": ci.quantity,
            "unit_price": unit_price,
        })
        total += unit_price * ci.quantity

    order = order_repository.create_order(user_id, items, total)
    cart_repository.clear_cart(user_id)
    return order


def buy_now(user_id: UUID, product_id: UUID) -> Order:
    """Create an order for a single product at quantity 1.

    Bypasses the cart entirely — creates an order directly for the given
    product (Requirement 5.2).  The unit_price is snapshotted from the
    product's current price.

    Args:
        user_id:    The UUID of the authenticated user.
        product_id: The UUID of the product to purchase.

    Returns:
        The newly created Order containing exactly one OrderItem for the
        given product with quantity=1 and unit_price=product.price.

    Raises:
        NotFoundError: If no active product with the given id exists.
    """
    product = product_repository.find_by_id(product_id)
    if product is None:
        raise NotFoundError("Product not found.")

    items = [{"product_id": product_id, "quantity": 1, "unit_price": product.price}]
    return order_repository.create_order(user_id, items, product.price)


def get_order_history(user_id: UUID) -> List[Order]:
    """Return all orders for the user sorted by created_at DESC.

    Delegates to order_repository.list_by_user() (Requirement 7.3).

    Args:
        user_id: The UUID of the authenticated user.

    Returns:
        A list of Order instances, each with ``items`` populated, ordered
        newest-first.  Returns an empty list when the user has no orders.
    """
    return order_repository.list_by_user(user_id)
