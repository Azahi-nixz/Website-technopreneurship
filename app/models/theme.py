from dataclasses import dataclass
from datetime import datetime


@dataclass
class ThemeConfig:
    accent_color: str       # hex, e.g. "#D4AF37"
    background_color: str   # hex, e.g. "#0A0E1A"
    font_family: str        # e.g. "Inter"
    updated_at: datetime
