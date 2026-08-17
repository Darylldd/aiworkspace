from dataclasses import dataclass

from app.db.database import get_connection


@dataclass
class Memory:
    id: int
    content: str


class MemoryStore:
    def save(self, workspace_id: int | None, content: str) -> Memory:
        connection = get_connection()
        try:
            cursor = connection.execute(
                "INSERT INTO memories (workspace_id, content) VALUES (?, ?)",
                (workspace_id, content),
            )
            connection.commit()
            return Memory(id=cursor.lastrowid, content=content)
        finally:
            connection.close()

    def list_for_workspace(self, workspace_id: int | None) -> list[Memory]:
        connection = get_connection()
        try:
            rows = connection.execute(
                "SELECT id, content FROM memories WHERE workspace_id IS ? ORDER BY id",
                (workspace_id,),
            ).fetchall()
            return [Memory(id=row["id"], content=row["content"]) for row in rows]
        finally:
            connection.close()