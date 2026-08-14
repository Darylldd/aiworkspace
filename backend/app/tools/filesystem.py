from typing import Any

from app.tools.base import Tool
from app.workspace.boundary import PathEscapesWorkspaceError, WorkspaceBoundary


class ListDirectoryTool(Tool):
    def __init__(self, boundary: WorkspaceBoundary) -> None:
        self._boundary = boundary

    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return "List files and folders inside the allowed workspace."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path relative to the workspace root. Use '.' for the root.",
                }
            },
            "required": ["path"],
        }

    async def execute(self, path: str = ".", **kwargs: Any) -> str:
        try:
            target = self._boundary.resolve(path)
        except PathEscapesWorkspaceError as error:
            return f"Error: {error}"

        if not target.is_dir():
            return f"Error: '{path}' is not a directory"

        entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
        lines = [f"{'file' if e.is_file() else 'dir '}  {e.name}" for e in entries]
        return "\n".join(lines) if lines else "(empty directory)"


class ReadFileTool(Tool):
    MAX_READ_BYTES = 100_000
    ENCODINGS_TO_TRY = ("utf-8", "utf-16", "cp1252")

    def __init__(self, boundary: WorkspaceBoundary) -> None:
        self._boundary = boundary

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "Read the contents of a text file inside the allowed workspace. "
            "For a file directly in the root, use just its filename, e.g. "
            "'requirements.txt' — do not prefix with './' or '/'."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file, relative to the workspace root.",
                }
            },
            "required": ["path"],
        }

    async def execute(self, path: str, **kwargs: Any) -> str:
        try:
            target = self._boundary.resolve(path)
        except PathEscapesWorkspaceError as error:
            return f"Error: {error}"

        if not target.is_file():
            return f"Error: '{path}' is not a file"

        content = self._read_with_fallback_encoding(target)
        if content is None:
            return f"Error: '{path}' could not be decoded as text"

        if len(content) > self.MAX_READ_BYTES:
            content = content[: self.MAX_READ_BYTES]
            content += "\n\n[... truncated, file is larger than the read limit ...]"

        return content

    def _read_with_fallback_encoding(self, target) -> str | None:
        for encoding in self.ENCODINGS_TO_TRY:
            try:
                return target.read_text(encoding=encoding)
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None


class SearchFilesTool(Tool):
    MAX_RESULTS = 50

    def __init__(self, boundary: WorkspaceBoundary) -> None:
        self._boundary = boundary

    @property
    def name(self) -> str:
        return "search_files"

    @property
    def description(self) -> str:
        return "Search for files by name pattern inside the allowed workspace."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern, e.g. '*.py' or '**/*.md'.",
                }
            },
            "required": ["pattern"],
        }

    async def execute(self, pattern: str, **kwargs: Any) -> str:
        matches = []
        for candidate in self._boundary.root.rglob(pattern):
            try:
                self._boundary.resolve(str(candidate.relative_to(self._boundary.root)))
            except PathEscapesWorkspaceError:
                continue

            matches.append(str(candidate.relative_to(self._boundary.root)))
            if len(matches) >= self.MAX_RESULTS:
                break

        if not matches:
            return f"No files matched pattern '{pattern}'"

        return "\n".join(matches)