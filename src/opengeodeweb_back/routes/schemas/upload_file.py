from dataclasses import dataclass
from typing import Optional


@dataclass
class UploadFile:
    filename: Optional[str] = None
