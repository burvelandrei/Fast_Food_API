from pydantic import BaseModel


class CategoryOut(BaseModel):
    id: int
    name: str