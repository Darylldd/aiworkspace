from typing import Any

from app.memory.memory_store import MemoryStore
from app.tools.base import Tool


class RememberTool(Tool):
    def __init__(self, store: MemoryStore, workspace_id: int | None) -> None:
        self._store = store
        self._workspace_id = workspace_id

    @property
    def name(self) -> str:
        return "remember"

    @property
    def description(self) -> str:
        return (
            "Save a fact for long-term recall in this workspace. Only "
            "call this when the user explicitly asks you to remember "
            "something — never save information the user has not "
            "clearly asked you to retain."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "description": "The specific fact to remember, stated clearly and concisely.",
                }
            },
            "required": ["fact"],
        }

    async def execute(self, fact: str, **kwargs: Any) -> str:
        self._store.save(self._workspace_id, fact)
        return f"Remembered: {fact}"


class RecallTool(Tool):
    def __init__(self, store: MemoryStore, workspace_id: int | None) -> None:
        self._store = store
        self._workspace_id = workspace_id

    @property
    def name(self) -> str:
        return "recall"

    @property
    def description(self) -> str:
        return "Retrieve all remembered facts for the current workspace."

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs: Any) -> str:
        memories = self._store.list_for_workspace(self._workspace_id)
        if not memories:
            return "No memories saved for this workspace yet."
        return "\n".join(f"- {m.content}" for m in memories)