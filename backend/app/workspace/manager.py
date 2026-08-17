import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.db.database import get_connection


@dataclass
class Workspace:
    id: int
    name: str
    path: str
    is_active: bool


class WorkspaceValidationError(Exception):
    pass


class WorkspaceManager:
    def create(self, name: str, path: str) -> Workspace:
        resolved_path = Path(path).resolve()
        if not resolved_path.is_dir():
            raise WorkspaceValidationError(f"Path does not exist or is not a directory: {path}")

        connection = get_connection()
        try:
            cursor = connection.execute(
                "INSERT INTO workspaces (name, path) VALUES (?, ?)",
                (name, str(resolved_path)),
            )
            connection.commit()
            return Workspace(
                id=cursor.lastrowid,
                name=name,
                path=str(resolved_path),
                is_active=False,
            )
        except sqlite3.IntegrityError as error:
            raise WorkspaceValidationError(f"A workspace named '{name}' already exists") from error
        finally:
            connection.close()

    def list_all(self) -> list[Workspace]:
        connection = get_connection()
        try:
            rows = connection.execute(
                "SELECT id, name, path, is_active FROM workspaces ORDER BY name"
            ).fetchall()
            return [
                Workspace(id=row["id"], name=row["name"], path=row["path"], is_active=bool(row["is_active"]))
                for row in rows
            ]
        finally:
            connection.close()

    def get_active(self) -> Workspace | None:
        connection = get_connection()
        try:
            row = connection.execute(
                "SELECT id, name, path, is_active FROM workspaces WHERE is_active = 1"
            ).fetchone()
            if row is None:
                return None
            return Workspace(id=row["id"], name=row["name"], path=row["path"], is_active=True)
        finally:
            connection.close()

    def set_active(self, workspace_id: int) -> Workspace:
        connection = get_connection()
        try:
            connection.execute("UPDATE workspaces SET is_active = 0")
            cursor = connection.execute(
                "UPDATE workspaces SET is_active = 1 WHERE id = ?", (workspace_id,)
            )
            if cursor.rowcount == 0:
                raise WorkspaceValidationError(f"No workspace with id {workspace_id}")
            connection.commit()

            row = connection.execute(
                "SELECT id, name, path, is_active FROM workspaces WHERE id = ?", (workspace_id,)
            ).fetchone()
            return Workspace(id=row["id"], name=row["name"], path=row["path"], is_active=True)
        finally:
            connection.close()