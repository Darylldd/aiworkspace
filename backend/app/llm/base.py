from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, message: str) -> str:
        """Send a message to the LLM and return its text response."""
        raise NotImplementedError