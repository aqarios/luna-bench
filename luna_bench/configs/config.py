from pydantic_settings import BaseSettings


class Config(BaseSettings):
    DB_CONNECTION_STRING: str = "luna_bench.db"


config = Config()
