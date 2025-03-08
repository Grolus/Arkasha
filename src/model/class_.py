from pydantic import BaseModel
from .user import User

class Class(BaseModel):
    name: str
    creator: User
    