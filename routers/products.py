from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.product import ProductOut
from db.operations import ProductDO


router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductOut])
async def get_products(
    category_id: int = Query(None),
    session: AsyncSession = Depends(get_session),
):
    products = await ProductDO.get_all(category_id=category_id, session=session)
    return products


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    product = await ProductDO.get_by_id(id=product_id, session=session)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
