"""
Data structures for survey point segmentation
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass
class SurveyPointData:
    """Represents a survey point with spatial and temporal attributes"""
    id: int
    x: float
    y: float
    timestamp: str
    responseid: str
    projectid: int
    description: Optional[str] = None
    radius: Optional[float] = None
    resolution: Optional[float] = None

    @property
    def coords(self) -> Tuple[float, float]:
        return (self.x, self.y)

    @property
    def datetime(self) -> datetime:
        """Parse timestamp to datetime object"""
        # Handle various timestamp formats
        try:
            # Try ISO format first
            return datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # Try Unix timestamp (milliseconds)
            try:
                return datetime.fromtimestamp(float(self.timestamp) / 1000)
            except (ValueError, TypeError):
                # Fallback to now if parsing fails
                return datetime.now()
