from pydantic import BaseModel, Field

class UserCreate(BaseModel):

    name:str = Field(...,min_length= 2, max_length= 50)
    age:int = Field(...,ge=1, le=120)
    email:str
    password:str = Field(..., min_length=6)
    role:str="user"
    image_url:str|None = None


class UserLogin(BaseModel):
    email:str
    password:str

class TokenReponse(BaseModel):
    access_token:str
    token_type:str = "bearer"


class UserUpdate(BaseModel):
    id:str | None = None
    name:str |None = None
    age:int | None = None
    email : str| None = None
    role : str | None = None
    image_url:str |None = None

class UserReponse(BaseModel):
    id:str
    name:str
    age:int
    email:str
    role:str
    image_url : str |None = None

class UserFilter(BaseModel):
    search:str |None = None
    min_age:int |None = None
    max_age: int |None = None
    sort_by: str="role"
    order: str="asc"
    role: str | None = None
    limit:int = 15
    skip:int = 0
    
