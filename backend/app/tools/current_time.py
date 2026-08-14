from datetime import datetime
from typing import Any

from app.tools.base import Tool


class CurrentTimeTool(Tool):
    @property
    def name(self) -> str:
        return "get_current_time"

    @property
    def description(self) -> str:
        return (
            "Get the current, real, live date and time. Always use this "
            "instead of guessing or citing a training cutoff when asked "
            "about the current date or time."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs: Any) -> str:
        return datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")