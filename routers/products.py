from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.product import ProductOut
from db.operations import ProductDO
from fastapi_cache.decorator import cache


router = APIRouter(prefix="/products", tags=["Products"])


# Роутер получения всех продуктов по категории (если category_id=None то выводит все продукты)
@router.get("/", response_model=list[ProductOut])
@cache(expire=60)
async def get_products(
    category_id: int = Query(None),
    session: AsyncSession = Depends(get_session),
):
    if not category_id:
        products = await ProductDO.get_all(session=session)
    else:
        products = await ProductDO.get_all_by_category_id(
            category_id=category_id, session=session
        )
    return products


# Роутер получения продукта по id
@router.get("/{product_id}/", response_model=ProductOut)
@cache(expire=60)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session),
):
    product = await ProductDO.get_by_id(product_id=product_id, session=session)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
