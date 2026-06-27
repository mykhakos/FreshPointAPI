from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from freshpointclient import PageClient
from freshpointparser.filters import ProductFilter
from freshpointparser.models import Product, ProductPage
from freshpointparser.parsers import ParseResult
from typing_extensions import Annotated

from ..additional_responses import (
    BAD_GATEWAY,
    GATEWAY_TIMEOUT,
    NOT_FOUND,
    NOT_MODIFIED,
    response_info_to_dict,
)
from ..dependencies.products import product_page_client, product_page_parse_result
from ..params import LocationIdPath, ProductIdPath
from ..tags import Tag

router = APIRouter(
    prefix="/locations/{locationId}",
    tags=[Tag.PRODUCTS],
    responses=response_info_to_dict(BAD_GATEWAY, GATEWAY_TIMEOUT, NOT_FOUND),
)


@router.get(
    "/allergens",
    responses=response_info_to_dict(NOT_MODIFIED),
    response_model_exclude_none=True,
)
async def list_allergens(
    result: ParseResult[ProductPage] = Depends(product_page_parse_result),
) -> List[str]:
    allergens = set()
    for allergen_list in result.page.iter_item_attr("allergens", unique=False):
        if allergen_list is not None:
            allergens.update(allergen_list)
    return sorted(allergens)


@router.get(
    "/categories",
    responses=response_info_to_dict(NOT_MODIFIED),
    response_model_exclude_none=True,
)
async def list_categories(
    result: ParseResult[ProductPage] = Depends(product_page_parse_result),
) -> List[str]:
    categories = (
        category
        for category in result.page.iter_item_attr("category", unique=True)
        if category is not None
    )
    return sorted(categories)


@router.get(
    "/products",
    responses=response_info_to_dict(NOT_MODIFIED),
    response_model_exclude_none=True,
)
async def list_products(
    filter_: Annotated[ProductFilter, Query()] = ProductFilter(),
    result: ParseResult[ProductPage] = Depends(product_page_parse_result),
) -> List[Product]:
    return list(result.page.find_items(filter_))


@router.post("/products/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh_products(
    client: PageClient[ProductPage] = Depends(product_page_client),
) -> None:
    await client.get(force_refresh=True)


@router.get(
    "/products/{productId}",
    responses=response_info_to_dict(NOT_MODIFIED),
    response_model_exclude_none=True,
)
async def get_product(
    location_id: LocationIdPath,  # kept for path params order
    product_id: ProductIdPath,
    result: ParseResult[ProductPage] = Depends(product_page_parse_result),
) -> Product:
    products = {prod.id_: prod for prod in result.page.items if prod.id_ is not None}
    try:
        return products[product_id]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
        ) from None
