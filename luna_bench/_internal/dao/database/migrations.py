"""What an existing database needs before the current tables can be used on it.

luna-bench creates its tables with ``CREATE TABLE IF NOT EXISTS``, which does nothing to
a table that is already there - a database written by an older version keeps the columns
it was written with, and the first query for a new one fails with ``no such column``.

The changes collected here are the ones a table can take in place: a column added with a
default that means "what this database already holds", and a unique index that now spans
one column more. Both are safe to apply to a database that has them already, so this runs
on every open rather than being tracked by a schema version.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from luna_bench.logging import BenchLogger

if TYPE_CHECKING:
    from peewee import Database


class _AddedColumn(NamedTuple):
    """A column a later version of luna-bench added to an existing table."""

    table: str
    column: str
    #: The column's type and default, as SQLite spells it. The default is what the rows
    #: already in the table mean: a benchmark written before repetitions existed ran every
    #: algorithm once, so its results are repetition 0.
    definition: str


class _WidenedIndex(NamedTuple):
    """A unique index that a later version of luna-bench widened by one column."""

    table: str
    #: The column the current index has and the old one does not. Every unique index on
    #: the table without it is stale and would refuse rows the new schema allows.
    #:
    #: The stale index is found this way rather than by name because peewee derives a
    #: name from the table and its columns, and hashes it once that grows past 64
    #: characters - so the old name is not something to write down with confidence.
    added_column: str


_ADDED_COLUMNS: tuple[_AddedColumn, ...] = (
    _AddedColumn("algorithmtable", "repetitions", "INTEGER NOT NULL DEFAULT 1"),
    _AddedColumn("algorithmresulttable", "repetition", "INTEGER NOT NULL DEFAULT 0"),
    _AddedColumn("metricresulttable", "repetition", "INTEGER NOT NULL DEFAULT 0"),
)

_WIDENED_INDEXES: tuple[_WidenedIndex, ...] = (
    _WidenedIndex("algorithmresulttable", "repetition"),
    _WidenedIndex("metricresulttable", "repetition"),
)

_logger = BenchLogger.get_logger(__name__)


def _table_exists(database: Database, table: str) -> bool:
    """Return whether *table* is present in the database.

    Parameters
    ----------
    database : Database
        The open database.
    table : str
        Name of the table.

    Returns
    -------
    bool
        Whether the table exists.
    """
    return table in set(database.get_tables())


def _columns(database: Database, table: str) -> set[str]:
    """Return the column names *table* currently has.

    Parameters
    ----------
    database : Database
        The open database.
    table : str
        Name of the table.

    Returns
    -------
    set[str]
        The column names.
    """
    return {column.name for column in database.get_columns(table)}


def migrate_schema(database: Database) -> None:
    """Bring an existing database up to the schema the current tables expect.

    Runs before the tables are created, so that ``create_tables`` afterwards adds what is
    genuinely missing - a new table, or the wider unique index whose stale version was
    dropped here. A database that is already current, and a database that is brand new,
    both come out of this untouched.

    Parameters
    ----------
    database : Database
        The open database to migrate in place.
    """
    for table, column, definition in _ADDED_COLUMNS:
        if not _table_exists(database, table) or column in _columns(database, table):
            continue
        _logger.info(f"Adding column '{column}' to table '{table}' of an older luna-bench database.")
        # Interpolation is safe here: every part of the statement is a literal from
        # _ADDED_COLUMNS, and SQLite takes no parameters in a DDL statement anyway.
        # peewee stubs leave `execute_sql` untyped; `unused-ignore` keeps environments where
        # mypy does not flag the call (with `warn_unused_ignores`) passing as well.
        database.execute_sql(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {definition}')  # type: ignore[no-untyped-call, unused-ignore]

    for table, added_column in _WIDENED_INDEXES:
        if not _table_exists(database, table):
            continue
        for index in database.get_indexes(table):
            # SQLite builds its own indexes for some constraints and refuses to drop them;
            # they are not ours to replace either.
            if not index.unique or index.name.startswith("sqlite_") or added_column in index.columns:
                continue
            _logger.info(f"Replacing the unique index '{index.name}' of table '{table}' with a wider one.")
            database.execute_sql(f'DROP INDEX IF EXISTS "{index.name}"')  # type: ignore[no-untyped-call, unused-ignore]
