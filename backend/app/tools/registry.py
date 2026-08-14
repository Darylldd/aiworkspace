from app.tools.base import Tool
from app.tools.current_time import CurrentTimeTool
from app.tools.filesystem import ListDirectoryTool, ReadFileTool, SearchFilesTool
from app.workspace.boundary import WorkspaceBoundary


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def to_groq_schemas(self) -> list[dict]:
        return [tool.to_groq_schema() for tool in self._tools.values()]


def build_default_registry(workspace_boundary: WorkspaceBoundary) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CurrentTimeTool())
    registry.register(ListDirectoryTool(workspace_boundary))
    registry.register(ReadFileTool(workspace_boundary))
    registry.register(SearchFilesTool(workspace_boundary))
    return registry