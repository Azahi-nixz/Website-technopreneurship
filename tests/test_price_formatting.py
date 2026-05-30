"""Property-based tests for the price formatting utility.

# Feature: commercial-ecommerce-website, Property 7: Price formatting always produces exactly two decimal places with currency symbol

**Validates: Requirements 3.4, 6.5**

For any non-negative numeric price value, ``format_price`` SHALL produce a
string that matches the pattern ``<currency_symbol><integer_part>.<two_digit_decimal>``
(e.g. ``$12.00``, ``$0.99``, ``$1234.50``).
"""

import re

from hypothesis import given
from hypothesis import strategies as st

from app.utils import format_price

# Regex that matches the required output format:
#   <currency_symbol> followed by one-or-more digits, a literal dot, then exactly two digits.
# The currency symbol is "$" (the default used by format_price).
_PRICE_PATTERN = re.compile(r"^\$\d+\.\d{2}$")


# ---------------------------------------------------------------------------
# Property 7 — price formatting always produces exactly two decimal places
#              with currency symbol
# ---------------------------------------------------------------------------

@given(st.decimals(min_value=0, max_value=99999, places=2, allow_nan=False, allow_infinity=False))
def test_format_price_matches_pattern(price):
    """Property 7: format_price output always matches <symbol><integer>.<two_digits>.

    **Validates: Requirements 3.4, 6.5**
    """
    result = format_price(price)
    assert _PRICE_PATTERN.match(result), (
        f"format_price({price!r}) returned {result!r}, "
        f"which does not match the expected pattern {_PRICE_PATTERN.pattern!r}"
    )


@given(st.decimals(min_value=0, max_value=99999, places=2, allow_nan=False, allow_infinity=False))
def test_format_price_starts_with_dollar_sign(price):
    """Property 7 (currency symbol): output always starts with '$'.

    **Validates: Requirements 3.4, 6.5**
    """
    result = format_price(price)
    assert result.startswith("$"), (
        f"format_price({price!r}) returned {result!r}, expected it to start with '$'"
    )


@given(st.decimals(min_value=0, max_value=99999, places=2, allow_nan=False, allow_infinity=False))
def test_format_price_has_exactly_two_decimal_places(price):
    """Property 7 (two decimal places): the fractional part is always exactly two digits.

    **Validates: Requirements 3.4, 6.5**
    """
    result = format_price(price)
    # Strip the leading currency symbol before splitting on the decimal point.
    numeric_part = result.lstrip("$")
    assert "." in numeric_part, (
        f"format_price({price!r}) returned {result!r}, which contains no decimal point"
    )
    integer_part, decimal_part = numeric_part.split(".", 1)
    assert len(decimal_part) == 2, (
        f"format_price({price!r}) returned {result!r}, "
        f"expected exactly 2 decimal digits but got {len(decimal_part)}: {decimal_part!r}"
    )
    assert decimal_part.isdigit(), (
        f"format_price({price!r}) returned {result!r}, "
        f"decimal part {decimal_part!r} contains non-digit characters"
    )
    assert integer_part.isdigit(), (
        f"format_price({price!r}) returned {result!r}, "
        f"integer part {integer_part!r} contains non-digit characters"
    )
