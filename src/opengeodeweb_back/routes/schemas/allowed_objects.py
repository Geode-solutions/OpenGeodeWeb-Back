from dataclasses import dataclass
from typing import Optional


@dataclass
class AllowedObjects:
    filename: str
    supported_feature: Optional[str] = None
