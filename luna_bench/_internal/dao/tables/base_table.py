from __future__ import annotations

from typing import Any

from peewee import Database, IntegrityError, Model, SqliteDatabase, sqlite3  # type: ignore[attr-defined]

from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

_database: Database = SqliteDatabase(None)


def setup_db_proxy(connection_string: str, tables: list[Any]) -> Database:
    if _database.is_closed():
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


class BaseTable(Model):
    class Meta:
        database = _database

    @staticmethod
    def map_integrity_error(error: IntegrityError) -> DataNotUniqueError | DataNotExistError | UnknownLunaBenchError:
        if isinstance(_database, SqliteDatabase):
            match error.orig.sqlite_errorcode:  # type: ignore[attr-defined]
                case sqlite3.SQLITE_CONSTRAINT_UNIQUE:
                    return DataNotUniqueError()
                case sqlite3.SQLITE_CONSTRAINT_NOTNULL:
                    return DataNotExistError()
                case _:  # pragma: no cover
                    return UnknownLunaBenchError(error)

        else:  # pragma: no cover
            raise NotImplementedError("Currently only SQLite for error handling is supported.")
