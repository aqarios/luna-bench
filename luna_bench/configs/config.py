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


config = Config()
