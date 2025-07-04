from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.models.product import Product
from app.routes.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])

# Example static product data
affiliate_products = [
    Product(title="Funny Meme Mug", image="https://memee.com/static/mug.jpg", link="https://memee.com/products/mug"),
    Product(title="Dank Meme T-Shirt", image="https://memee.com/static/tshirt.jpg", link="https://memee.com/products/tshirt"),
]

@router.get("/", response_model=List[Product])
def get_products(user=Depends(get_current_user)):
    try:
        return affiliate_products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 