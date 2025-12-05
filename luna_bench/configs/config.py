from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """
    Configuration for the application.

    Attributes
    ----------
    DB_CONNECTION_STRING : str
        Connection string for the database. Example: "luna_bench.db".
    """

    DB_CONNECTION_STRING: str = "luna_bench.db"
    DB_JOBS_CONNECTION_STRING: str = "luna_bench-jobs.db"

    ALGORITHM_INTERNAL_BACKOFF_TIME: float = 0.001

    ASYNC_WORKER_COUNT: int = 10


config = Config()
