from fastapi import APIRouter, Depends, HTTPException, status
from ..schemas.delivery_partner import DeliveryPartnerCreate
from ..dependencies import SellerServiceDep, SessionDep, get_partner_access_token, DeliveryPartnerDep, DeliveryPartnerServiceDep
from ..schemas.delivery_partner import DeliveryPartnerRead, DeliveryPartnerUpdate
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.core.security import oauth2_scheme
from app.utils import decode_access_token
from app.database.models import Seller
from app.database.redis import add_jti_to_blacklist

router = APIRouter(prefix="/partner", tags=["Delivery Partner"])

@router.post("/signup", response_model= DeliveryPartnerRead)
async def register_delivery_partner(
    seller: DeliveryPartnerCreate,
    service: DeliveryPartnerServiceDep,
):
    return await service.add(seller)


#Login the delivery partner
@router.post("/token")
async def login_delivery_partner(
    request_form: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: DeliveryPartnerServiceDep,
):
    token = await service.token(request_form.username, request_form.password)
    return {
        "access_token": token,
        "type": "jwt",
    }

#Update Delivery Partner
@router.post("/", response_model=DeliveryPartnerRead)
async def update_delivery_partner(
    partner_update: DeliveryPartnerUpdate,
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    return await service.update(
        partner.sqlmodel_update(partner_update)
    ) 

#Logout the delivery partner
@router.get("/logout")
async def logout_delivery_partner(
    token_data: Annotated[dict, Depends(get_partner_access_token)],
):
    await add_jti_to_blacklist(token_data["jti"])
    return {
        "detail": "Successfully logged out"
    }