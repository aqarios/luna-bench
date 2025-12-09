import os

os.environ["DB_CONNECTION_STRING"] = ":memory:"  # Otherwise we create a db file each time we run tests
os.environ["DB_JOBS_CONNECTION_STRING"] = ":memory:"  # Otherwise we create a db file each time we run tests
