from pydantic import BaseModel


class Plot(BaseModel):
    def run(self) -> None: ...
