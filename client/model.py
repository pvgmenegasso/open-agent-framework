from pydantic import BaseModel


class Model(BaseModel):
    name: str
    id: str
    size: str
    modified: str