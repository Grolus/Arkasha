from pydantic import BaseModel
from .subject import Subject

class Lesson(BaseModel):
    subject: Subject
    
    
    