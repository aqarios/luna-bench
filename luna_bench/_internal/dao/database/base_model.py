from __future__ import annotations

from typing import Any

from peewee import Database, Model, SqliteDatabase

_database: Database = SqliteDatabase(None)


def setup_db_proxy(connection_string: str, tables: list[Any]) -> Database:
    _database.init(
        connection_string,
        pragmas=(
            ("cache_size", -1024 * 64),  # 64MB page-cache.
            ("journal_mode", "wal"),  # Use WAL-mode (you should always use this!).
            ("foreign_keys", 1),  # Enforce foreign-key constraints.
        ),
    )
    _database.create_tables(tables, safe=True)

    return _database


class BaseModel(Model):
    class Meta:
        database = _database
