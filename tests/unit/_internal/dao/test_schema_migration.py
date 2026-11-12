"""A database written before repetitions existed has to keep working."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from peewee import SqliteDatabase

from luna_bench._internal.dao.database.migrations import migrate_schema

if TYPE_CHECKING:
    from pathlib import Path

#: The two tables as an older luna-bench wrote them: no repetition column, and a unique
#: index one column narrower than the current one.
_OLD_SCHEMA = (
    """
    CREATE TABLE "algorithmtable" (
        "id" INTEGER NOT NULL PRIMARY KEY,
        "name" VARCHAR(45) NOT NULL,
        "registered_id" VARCHAR(255) NOT NULL
    )
    """,
    """
    CREATE TABLE "algorithmresulttable" (
        "id" INTEGER NOT NULL PRIMARY KEY,
        "status" VARCHAR(16) NOT NULL,
        "algorithm_id" INTEGER NOT NULL,
        "model_metadata_id" INTEGER NOT NULL
    )
    """,
    """
    CREATE UNIQUE INDEX "algorithmresulttable_model_metadata_id_algorithm_id"
    ON "algorithmresulttable" ("model_metadata_id", "algorithm_id")
    """,
    """
    CREATE TABLE "metricresulttable" (
        "id" INTEGER NOT NULL PRIMARY KEY,
        "status" VARCHAR(16) NOT NULL,
        "metric_id" INTEGER NOT NULL,
        "algorithm_id" INTEGER NOT NULL,
        "model_metadata_id" INTEGER NOT NULL
    )
    """,
    # Named as peewee named it: past 64 characters it truncates and appends a hash of the
    # full name, which is why the migration finds a stale index by its columns, not by name.
    """
    CREATE UNIQUE INDEX "metricresulttable_model_metadata_id_metric_id_algorithm__d70ee41"
    ON "metricresulttable" ("model_metadata_id", "metric_id", "algorithm_id")
    """,
)


def execute(database: SqliteDatabase, statement: str) -> Any:  # noqa: ANN401 # Whatever the cursor returns.
    """Run one statement, past peewee's untyped ``execute_sql``.

    Parameters
    ----------
    database : SqliteDatabase
        The open database.
    statement : str
        The SQL to run.

    Returns
    -------
    Any
        The cursor the statement produced.
    """
    # peewee stubs leave `execute_sql` untyped; `unused-ignore` keeps environments where
    # mypy does not flag the call (with `warn_unused_ignores`) passing as well.
    return database.execute_sql(statement)  # type: ignore[no-untyped-call, unused-ignore]


@pytest.fixture()
def old_database(tmp_path: Path) -> SqliteDatabase:
    """Return an open database holding one row per table, in the pre-repetitions schema."""
    database = SqliteDatabase(str(tmp_path / "old.db"))
    database.connect()
    for statement in _OLD_SCHEMA:
        execute(database, statement)
    execute(database, "INSERT INTO \"algorithmtable\" VALUES (1, 'scip', 'scip_id')")
    execute(database, "INSERT INTO \"algorithmresulttable\" VALUES (1, 'DONE', 1, 1)")
    execute(database, "INSERT INTO \"metricresulttable\" VALUES (1, 'DONE', 1, 1, 1)")
    return database


def _columns(database: SqliteDatabase, table: str) -> set[str]:
    return {column.name for column in database.get_columns(table)}


def _indexes(database: SqliteDatabase, table: str) -> set[str]:
    return {index.name for index in database.get_indexes(table)}


class TestSchemaMigration:
    def test_the_new_columns_are_added_with_what_the_old_rows_mean(self, old_database: SqliteDatabase) -> None:
        migrate_schema(old_database)

        assert "repetitions" in _columns(old_database, "algorithmtable")
        assert "repetition" in _columns(old_database, "algorithmresulttable")
        assert "repetition" in _columns(old_database, "metricresulttable")

        # A benchmark written before repetitions existed ran everything once.
        assert execute(old_database, 'SELECT "repetitions" FROM "algorithmtable"').fetchone() == (1,)
        assert execute(old_database, 'SELECT "repetition" FROM "algorithmresulttable"').fetchone() == (0,)
        assert execute(old_database, 'SELECT "repetition" FROM "metricresulttable"').fetchone() == (0,)

    def test_the_narrower_unique_indexes_are_dropped(self, old_database: SqliteDatabase) -> None:
        """They would refuse the second run of an algorithm on a model."""
        migrate_schema(old_database)

        assert "algorithmresulttable_model_metadata_id_algorithm_id" not in _indexes(
            old_database, "algorithmresulttable"
        )
        # Found by its columns, so the hashed name peewee gave it does not matter.
        assert "metricresulttable_model_metadata_id_metric_id_algorithm__d70ee41" not in _indexes(
            old_database, "metricresulttable"
        )

    def test_an_index_that_already_covers_the_repetition_is_kept(self, old_database: SqliteDatabase) -> None:
        """Only the narrower ones go - a current database keeps the index it has."""
        migrate_schema(old_database)
        execute(
            old_database,
            'CREATE UNIQUE INDEX "current" ON "algorithmresulttable" '
            '("model_metadata_id", "algorithm_id", "repetition")',
        )

        migrate_schema(old_database)

        assert "current" in _indexes(old_database, "algorithmresulttable")

    def test_a_second_run_of_the_same_pair_fits_afterwards(self, old_database: SqliteDatabase) -> None:
        migrate_schema(old_database)

        execute(old_database, "INSERT INTO \"algorithmresulttable\" VALUES (2, 'DONE', 1, 1, 1)")

        rows = execute(old_database, 'SELECT "repetition" FROM "algorithmresulttable" ORDER BY "id"').fetchall()
        assert rows == [(0,), (1,)]

    def test_running_it_twice_changes_nothing(self, old_database: SqliteDatabase) -> None:
        """It runs on every open, so it has to be safe on a database that is current."""
        migrate_schema(old_database)
        before = _columns(old_database, "algorithmresulttable")

        migrate_schema(old_database)

        assert _columns(old_database, "algorithmresulttable") == before

    def test_an_empty_database_is_left_alone(self, tmp_path: Path) -> None:
        """A brand new database has no tables yet - they are created after this runs."""
        database = SqliteDatabase(str(tmp_path / "new.db"))
        database.connect()

        migrate_schema(database)

        assert database.get_tables() == []
