from pydantic import BaseModel, HttpUrl
 
class Product(BaseModel):
    title: str
    image: HttpUrl
    link: HttpUrl 