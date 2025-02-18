from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db.connect import get_session
from schemas.product import ProductOut
from db.operations import ProductDO


router = APIRouter("/product", tags=["Product"])


@router.get("/", response_model=list[ProductOut])
async def get_products(session: AsyncSession = Depends(get_session)):
    products = await ProductDO.get_all(session=session)
    return products


@router.get("/{id}", response_class=ProductDO)
async def get_product(id: int, session: AsyncSession = Depends(get_session)):
    product = await ProductDO.get_by_id(id=id, session=session)
    return product