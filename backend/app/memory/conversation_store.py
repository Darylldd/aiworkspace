from dataclasses import dataclass

from app.db.database import get_connection


@dataclass
class Message:
    role: str
    content: str


class ConversationStore:
    def create_conversation(self, workspace_id: int | None) -> int:
        connection = get_connection()
        try:
            cursor = connection.execute(
                "INSERT INTO conversations (workspace_id) VALUES (?)", (workspace_id,)
            )
            connection.commit()
            return cursor.lastrowid
        finally:
            connection.close()

    def add_message(self, conversation_id: int, role: str, content: str) -> None:
        connection = get_connection()
        try:
            connection.execute(
                "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, role, content),
            )
            connection.commit()
        finally:
            connection.close()

    def get_messages(self, conversation_id: int) -> list[Message]:
        connection = get_connection()
        try:
            rows = connection.execute(
                "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id",
                (conversation_id,),
            ).fetchall()
            return [Message(role=row["role"], content=row["content"]) for row in rows]
        finally:
            connection.close()