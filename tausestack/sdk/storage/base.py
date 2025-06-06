# Base classes for storage backends
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class AbstractJsonStorageBackend(ABC):
    """Abstract Base Class for JSON storage backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a JSON object by key."""
        pass

    @abstractmethod
    def put(self, key: str, value: Dict[str, Any]) -> None:
        """Store a JSON object by key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete a JSON object by key."""
        pass
