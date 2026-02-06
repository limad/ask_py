# lambda/schemas.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class QuestionState:
    """Represents a question state from Jeedom."""
    event_id: Optional[str]
    text: str
    suppress_confirmation: bool = False
    deviceSerialNumber: Optional[str] = None
    textBrut: Optional[str] = None


@dataclass
class QuestionStateError:
    """Represents an error state."""
    text: str