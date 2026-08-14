from pathlib import Path


class PathEscapesWorkspaceError(Exception):
    def __init__(self, requested_path: str) -> None:
        self.requested_path = requested_path
        super().__init__(
            f"Path '{requested_path}' is outside the allowed workspace"
        )


class WorkspaceBoundary:
    """
    Confines filesystem access to a single root directory.
    Every path a tool wants to touch must be resolved through here first.
    """

    def __init__(self, root: str) -> None:
        self._root = Path(root).resolve()
        if not self._root.is_dir():
            raise ValueError(f"Workspace root does not exist: {root}")

    @property
    def root(self) -> Path:
        return self._root

    def resolve(self, relative_path: str) -> Path:
        candidate = (self._root / relative_path).resolve()

        if not self._is_within_root(candidate):
            raise PathEscapesWorkspaceError(relative_path)

        return candidate

    def _is_within_root(self, candidate: Path) -> bool:
        try:
            candidate.relative_to(self._root)
            return True
        except ValueError:
            return False