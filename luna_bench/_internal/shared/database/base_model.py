from peewee import Model, SqliteDatabase

from luna_bench.configs.config import config

database = SqliteDatabase(
config.DB_CONNECTION_STRING,
    ":memory:",
    pragmas=(
        ("cache_size", -1024 * 64),  # 64MB page-cache.
        ("journal_mode", "wal"),  # Use WAL-mode (you should always use this!).
        ("foreign_keys", 1),
    ),
)  # Enforce foreign-key constraints.


class BaseModel(Model):
    class Meta:
        database = database
