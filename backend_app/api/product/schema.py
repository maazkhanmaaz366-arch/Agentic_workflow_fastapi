from pydantic import BaseModel, Field


class CreateProduct(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    price: float = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=2, max_length=50)
    description: str | None = Field(None, min_length=5, max_length=200)
    image_url: str | None = None


class UpdateProduct(BaseModel):
    id: str | None = None
    name: str | None = None
    price: float | None = None
    stock: int | None = None
    category: str | None = None
    description: str | None = None
    image_url: str | None = None


class ReponseProduct(BaseModel):
    id: str
    name: str
    price: float
    stock: int
    description: str | None
    image_url: str | None = None



class FilterProducts(BaseModel):
    search:str |None =None
    category:str |None = None
    min_price:float |None = None
    max_price:float |None = None
    sort_by:str = "price"
    order:str = "asc"
    skip:int = 0
    limit:int = 10