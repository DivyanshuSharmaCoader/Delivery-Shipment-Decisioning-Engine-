from fastapi import APIRouter, Depends

from app.core.exceptions import NothingToUpdate
from ..schemas.delivery_partner import DeliveryPartnerCreate
from ..dependencies import SellerServiceDep, SessionDep, get_partner_access_token, DeliveryPartnerDep, DeliveryPartnerServiceDep
from ..schemas.delivery_partner import DeliveryPartnerRead, DeliveryPartnerUpdate
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.database.redis import add_jti_to_blacklist
from app.api.tag import APITag

router = APIRouter(prefix="/partner", tags=[APITag.PARTNER])

#Register a delivery partner
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

#Verify seller Email
@router.get("/verify")
async def verify_delivery_partner_email(token: str, service: DeliveryPartnerServiceDep,):
    await service.verify_email(token)
    return {"detail": "Account Verified"}

#Update Delivery Partner
@router.post("/", response_model=DeliveryPartnerRead)
async def update_delivery_partner(
    partner_update: DeliveryPartnerUpdate,
    partner: DeliveryPartnerDep,
    service: DeliveryPartnerServiceDep,
):
    # Update data with given fields
    update = partner_update.model_dump(exclude_none=True)

    if not update:
        raise NothingToUpdate()
    
    return await service.update(
        partner.sqlmodel_update(update)
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