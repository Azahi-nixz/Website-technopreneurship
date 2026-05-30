from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID


@dataclass
class ProductImage:
    id: UUID
    product_id: UUID
    image_url: str
    display_order: int


@dataclass
class Product:
    id: UUID
    name: str
    description: Optional[str]
    price: Decimal
    is_active: bool
    created_at: datetime
    images: List[ProductImage] = field(default_factory=list)
