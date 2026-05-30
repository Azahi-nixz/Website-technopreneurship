from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class CartItem:
    id: UUID
    user_id: UUID
    product_id: UUID
    quantity: int
    updated_at: datetime
    product: Optional[object] = None  # Product, injected for display
