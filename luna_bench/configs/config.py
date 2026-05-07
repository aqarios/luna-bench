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

    LB_DB_CONNECTION_STRING: str = "luna_bench.db"
    LB_DB_JOBS_CONNECTION_STRING: str = "luna_bench-jobs.db"

    LB_ALGORITHM_INTERNAL_BACKOFF_TIME: float = 0.001

    LB_ASYNC_WORKER_COUNT: int = 10

    LB_HUEY_WORKER_TYPE: Literal["process", "thread", "greenlet"] | None = None
    LB_HUEY_JOIN_TIMEOUT: int = 10


config = Config()
