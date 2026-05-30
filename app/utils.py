"""Utility functions for the e-commerce application.

Requirements: 3.4, 6.5
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union


def format_price(price: Union[Decimal, float, int, str], currency_symbol: str = "$") -> str:
    """Format a numeric price value as a currency string with exactly two decimal places.

    For any non-negative numeric price value, produces a string matching the
    pattern ``<currency_symbol><integer_part>.<two_digit_decimal>``
    (e.g. ``$12.00``, ``$0.99``, ``$1234.50``).

    Args:
        price: A non-negative numeric value representing a price.
        currency_symbol: The currency symbol to prepend (default ``"$"``).

    Returns:
        A string of the form ``<symbol><integer>.<two_digits>``.

    Raises:
        ValueError: If *price* is negative.

    Requirements: 3.4, 6.5
    """
    value = Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if value < 0:
        raise ValueError(f"Price must be non-negative, got {value}")
    return f"{currency_symbol}{value}"
