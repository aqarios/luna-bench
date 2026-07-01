from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Configuration for the application.

    Attributes
    ----------
    LB_DB_CONNECTION_STRING : str
        Connection string for the database. Example: "luna_bench.db".
    LB_HUEY_WORKER_TYPE : Literal["process", "thread", "greenlet"] | None
        Override the automatically detected worker type for Huey background tasks.
        Valid values: "process", "thread", or "greenlet". If not set, the worker type
        is auto-detected based on the operating system (process for Unix/Linux, thread for Windows).
    """

    LB_DB_CONNECTION_STRING: str = ""
    LB_DB_JOBS_CONNECTION_STRING: str = ""

    LB_ALGORITHM_INTERNAL_BACKOFF_TIME: float = 0.001

    LB_ASYNC_WORKER_COUNT: int = 2

    LB_HUEY_WORKER_TYPE: Literal["process", "thread", "greenlet"] | None = None
    LB_HUEY_JOIN_TIMEOUT: int = 10

    LB_DATA_DIR: str = "./benchmark_data"

    @property
    def resolved_db_connection_string(self) -> str:
        """Full path for the main benchmark database."""
        if self.LB_DB_CONNECTION_STRING:
            return self.LB_DB_CONNECTION_STRING
        return str(Path(self.LB_DATA_DIR) / "database" / "luna_bench.db")

    @property
    def resolved_jobs_db_connection_string(self) -> str:
        """Full path for the Huey jobs database."""
        if self.LB_DB_JOBS_CONNECTION_STRING:
            return self.LB_DB_JOBS_CONNECTION_STRING
        return str(Path(self.LB_DATA_DIR) / "database" / "luna_bench-jobs.db")


config = Config()
