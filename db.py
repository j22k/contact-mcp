"""SQLite access layer for the contacts table."""

import logging
import sqlite3

from config import DATABASE_PATH

logger = logging.getLogger("mcp-server")


def initialize_database() -> None:
    with sqlite3.connect(DATABASE_PATH) as connection:
        columns = connection.execute("PRAGMA table_info(contacts)").fetchall()
        email_column = next((column for column in columns if column[1] == "email"), None)

        if email_column and email_column[3]:
            connection.execute(
                """
                CREATE TABLE contacts_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    email TEXT UNIQUE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                INSERT INTO contacts_new (id, name, phone_number, email, created_at)
                SELECT id, name, phone_number, email, created_at FROM contacts
                """
            )
            connection.execute("DROP TABLE contacts")
            connection.execute("ALTER TABLE contacts_new RENAME TO contacts")

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                email TEXT UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    logger.info("Database initialized successfully at %s", DATABASE_PATH)


def insert_contact_row(name: str, phone_number: str, email: str | None) -> int:
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO contacts (name, phone_number, email) VALUES (?, ?, ?)",
            (name, phone_number, email),
        )
        return cursor.lastrowid


def delete_contact_row(contact_id: int) -> bool:
    with sqlite3.connect(DATABASE_PATH) as connection:
        cursor = connection.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        return cursor.rowcount > 0


def fetch_contacts() -> list[tuple]:
    with sqlite3.connect(DATABASE_PATH) as connection:
        return connection.execute(
            """
            SELECT id, name, phone_number, email, created_at
            FROM contacts
            ORDER BY id DESC
            """
        ).fetchall()
