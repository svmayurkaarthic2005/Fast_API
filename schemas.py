from pydantic import BaseModel
# pydantic module
# validation
# serialization
# documentation

class TodoBase(BaseModel):
    title: str
    description: str|None = None
    completed: bool = False

class TodoCreate(TodoBase): #Used when the client creates a Todo.
    pass
#It inherits:
# title
# description
# completed
# It doesn't need id because the database generates the ID.
   
class Todo(TodoBase):
    id: int

    class Config:
    #order to convert pydantic model to orm model
        # orm_mode=True   
        from_attributes=True
