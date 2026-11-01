import sqlite3
from pathlib import Path


# Database configuration
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "chat_history.db"


# 1. Database connection
def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# 2. Initialize database
def initialize_database():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE,
                CHECK (role IN ('user', 'assistant'))
            )
        """)

        connection.commit()

    finally:
        connection.close()


# 3. Create conversation
def create_conversation(title="New Chat"):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title,)
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        connection.close()


# 4. Save message
def save_message(conversation_id, role, content):
    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role")

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO messages (conversation_id, role, content)
            VALUES (?, ?, ?)
        """, (conversation_id, role, content))

        cursor.execute("""
            UPDATE conversations
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (conversation_id,))

        if role == "user":
            cursor.execute("""
                SELECT COUNT(*)
                FROM messages
                WHERE conversation_id = ?
                AND role = 'user'
            """, (conversation_id,))

            count = cursor.fetchone()[0]

            if count == 1:
                title = content[:50]

                cursor.execute("""
                    UPDATE conversations
                    SET title = ?
                    WHERE id = ?
                """, (title, conversation_id))

        connection.commit()

    finally:
        connection.close()


# 5. Get all conversations
def get_conversations():
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM conversations
            ORDER BY updated_at DESC, id DESC
        """)

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# 6. Get conversation messages
def get_messages(conversation_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT *
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
        """, (conversation_id,))

        return [dict(row) for row in cursor.fetchall()]

    finally:
        connection.close()


# 7. Delete conversation
def delete_conversation(conversation_id):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    finally:
        connection.close()