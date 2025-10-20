from dataclasses import dataclass
from typing import Optional


@dataclass
class AllowedFiles:
    supported_feature: Optional[str] = None
