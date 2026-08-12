from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, message: str) -> str:
        """Send a message to the LLM and return its full text response."""
        raise NotImplementedError

    @abstractmethod
    def stream(self, message: str) -> AsyncIterator[str]:
        """Send a message to the LLM and yield response text incrementally."""
        raise NotImplementedError