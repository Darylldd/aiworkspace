from app.memory.memory_store import MemoryStore
from app.terminal.executor import CommandExecutor
from app.tools.base import Tool
from app.tools.current_time import CurrentTimeTool
from app.tools.filesystem import ListDirectoryTool, ReadFileTool, SearchFilesTool
from app.tools.memory import RecallTool, RememberTool
from app.tools.project_info import ProjectInfoTool
from app.tools.terminal import RunCommandTool
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


def build_default_registry(
    workspace_boundary: WorkspaceBoundary, workspace_id: int | None = None
) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(CurrentTimeTool())
    registry.register(ListDirectoryTool(workspace_boundary))
    registry.register(ReadFileTool(workspace_boundary))
    registry.register(SearchFilesTool(workspace_boundary))
    registry.register(ProjectInfoTool(workspace_boundary))

    command_executor = CommandExecutor(working_directory=str(workspace_boundary.root))
    registry.register(RunCommandTool(command_executor))

    memory_store = MemoryStore()
    registry.register(RememberTool(memory_store, workspace_id))
    registry.register(RecallTool(memory_store, workspace_id))

    return registry