import subprocess
from pathlib import Path
from typing import Any

from app.tools.base import Tool
from app.workspace.boundary import WorkspaceBoundary


class ProjectInfoTool(Tool):
    MANIFEST_MARKERS = {
        "package.json": "npm/Node.js",
        "requirements.txt": "pip/Python",
        "pyproject.toml": "Python (pyproject)",
        "Cargo.toml": "Cargo/Rust",
        "go.mod": "Go modules",
    }

    def __init__(self, boundary: WorkspaceBoundary) -> None:
        self._boundary = boundary

    @property
    def name(self) -> str:
        return "get_project_info"

    @property
    def description(self) -> str:
        return "Get an overview of the current project: framework, package manager, git branch, and README summary."

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs: Any) -> str:
        root = self._boundary.root
        lines = [f"Project root: {root}"]

        lines.append(self._detect_package_managers(root))
        lines.append(self._detect_git_branch(root))
        lines.append(self._read_readme_summary(root))

        return "\n".join(part for part in lines if part)

    def _detect_package_managers(self, root: Path) -> str:
        found = []

        for filename, label in self.MANIFEST_MARKERS.items():
            if (root / filename).exists():
                found.append(f"{label} (root)")

        for subdir in root.iterdir():
            if not subdir.is_dir() or subdir.name.startswith("."):
                continue
            for filename, label in self.MANIFEST_MARKERS.items():
                if (subdir / filename).exists():
                    found.append(f"{label} ({subdir.name}/)")

        if not found:
            return "Package manager: none detected"
        return f"Package manager(s) detected: {', '.join(found)}"

    def _detect_git_branch(self, root: Path) -> str:
        git_dir = root / ".git"
        if not git_dir.exists():
            return "Git: not a git repository"

        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=root,
                capture_output=True,
                timeout=5,
            )
            branch = result.stdout.decode(errors="replace").strip()
            return f"Git branch: {branch}" if branch else "Git: repository present, branch unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Git: repository present, but git command unavailable"

    def _read_readme_summary(self, root: Path) -> str:
        for filename in ("README.md", "README.txt", "readme.md"):
            readme_path = root / filename
            if readme_path.exists():
                try:
                    content = readme_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    content = readme_path.read_text(encoding="utf-16", errors="replace")
                summary = content.strip().splitlines()[0] if content.strip() else "(empty)"
                return f"README found ({filename}), first line: {summary}"
        return "README: none found"