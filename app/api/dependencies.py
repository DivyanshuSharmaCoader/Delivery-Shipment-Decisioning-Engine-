from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.services.shipment import ShipmentService
from app.services.seller import SellerService
from app.core.security import oauth2_scheme_partner, oauth2_scheme_seller
from app.utils import decode_access_token
from app.database.models import Seller, DeliveryPartner
from app.database.redis import is_jti_blacklisted
from uuid import UUID
from app.services.delivery_partner import DeliveryPartnerService


# Asynchronous database session dep annotation
SessionDep = Annotated[AsyncSession, Depends(get_session)]

#Access Token data dep
async def _get_access_token(token: str) -> dict:
    data = decode_access_token(token)
    if data is None or await is_jti_blacklisted(data["jti"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
        )
    return data

#Seller Access Token Data
async def get_seller_access_token(token: Annotated[str, Depends(oauth2_scheme_seller)],) -> dict:
    return await _get_access_token(token)

#Delivery Partner Access Token Data
async def get_partner_access_token(token: Annotated[str, Depends(oauth2_scheme_partner)],) -> dict:
    return await _get_access_token(token)


#Logged in seller
async def get_current_seller(token_data: Annotated[dict, Depends(get_seller_access_token)], session: SessionDep,):
    seller = await session.get(Seller, UUID(token_data["user"]["id"]))
    if seller is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not Authorised",
        )
    return seller


#Logged in delivery partner
async def get_current_partner(token_data: Annotated[dict, Depends(get_partner_access_token)], session: SessionDep,):
    partner = await session.get(DeliveryPartner, UUID(token_data["user"]["id"]))
    if partner is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not Authorised",
        )
    return partner


# Shipment service dep
def get_shipment_service(session: SessionDep):

    return ShipmentService(session)

#Delivery partner service dep
def get_delivery_partner_service(session: SessionDep):
    return DeliveryPartnerService(session)

# Seller service dep
def get_seller_service(session: SessionDep):
    return SellerService(session, DeliveryPartnerService(session),)

#Seller dep
SellerDep = Annotated[Seller, Depends(get_current_seller),]

#Delivery Partner dep
DeliveryPartnerDep = Annotated[DeliveryPartner, Depends(get_current_partner),]

# Shipment service dep annotation
ServiceDep = Annotated[
    ShipmentService,
    Depends(get_shipment_service),
]


# Seller service dep annotation
SellerServiceDep = Annotated[
    SellerService,
    Depends(get_seller_service),
]


#Delivery Partner Service dep annotation
DeliveryPartnerServiceDep = Annotated[
    DeliveryPartnerService,
    Depends(get_delivery_partner_service),
]