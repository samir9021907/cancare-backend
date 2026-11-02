"""
Agro-Medical Stores & Krishi Seva Kendra Router (/api/v1/shops).

Public and farmer-accessible endpoint to search nearest authorized agricultural
medicine dealers, bio-control dispensaries, and Krishi Vigyan Kendra depots.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Request
from app import schemas
from app.services.shop_service import find_nearest_shops, resolve_farmer_location

router = APIRouter(prefix="/api/v1/shops", tags=["Agro-Medical Stores"])


@router.get(
    "",
    response_model=List[schemas.AgroShopItem],
    summary="Find nearest agro-medical stores & Krishi Seva Kendras",
    description="Returns authorized agricultural medicine shops sorted by proximity to the farmer's live location."
)
def get_nearest_agro_shops(
    request: Request,
    latitude: Optional[float] = Query(None, description="Farmer GPS latitude (auto-detected if omitted)"),
    longitude: Optional[float] = Query(None, description="Farmer GPS longitude"),
    district: Optional[str] = Query(None, description="District name (e.g. Kopargaon, Sangli, Kolhapur)"),
    pincode: Optional[str] = Query(None, description="Postal pincode"),
    limit: int = Query(5, ge=1, le=20, description="Maximum number of stores to return")
):
    client_ip = request.client.host if request.client else None
    loc = resolve_farmer_location(user_lat=latitude, user_lon=longitude, client_ip=client_ip)

    shops = find_nearest_shops(
        user_lat=loc["latitude"],
        user_lon=loc["longitude"],
        pincode=pincode or loc.get("pincode"),
        district=district or loc.get("district"),
        limit=limit
    )
    return [schemas.AgroShopItem(**s) for s in shops]

