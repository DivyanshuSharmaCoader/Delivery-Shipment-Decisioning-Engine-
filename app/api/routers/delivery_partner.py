from fastapi import APIRouter, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from pydantic import EmailStr

from app.config import app_settings
from app.core.exceptions import NothingToUpdate
from app.utils import TEMPLATE_DIR
from ..schemas.delivery_partner import DeliveryPartnerCreate
from ..dependencies import SellerServiceDep, SessionDep, get_partner_access_token, DeliveryPartnerDep, DeliveryPartnerServiceDep
from ..schemas.delivery_partner import DeliveryPartnerRead, DeliveryPartnerUpdate
from ..schemas.shipment import ShipmentRead
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

### Get delivery partner profile
@router.get("/me", response_model=DeliveryPartnerRead)
async def get_delivery_partner_profile(partner: DeliveryPartnerDep):
    return partner


### Get all shipments assigned to the delivery partner
@router.get("/shipments", response_model=list[ShipmentRead])
async def get_assigned_shipments(partner: DeliveryPartnerDep):
    return partner.shipments

#Verify partner Email
@router.get("/verify")
async def verify_delivery_partner_email(token: str, service: DeliveryPartnerServiceDep,):
    await service.verify_email(token)
    return {"detail": "Account Verified"}


#Email Password reset link
@router.get("/forgot_password")
async def forgot_password(email: EmailStr, service: DeliveryPartnerServiceDep):
    await service.send_password_reset_link(email, router.prefix)
    return {"detail": "Check email for password reset link"}


#Password Reset Form
@router.get("/reset_password_form")
async def get_reset_password_form(request: Request, token: str):
    templates = Jinja2Templates(TEMPLATE_DIR)
    return templates.TemplateResponse(
        request = request,
        name = "reset_password.html",
        context={
            "reset_url": f"https://{app_settings.APP_DOMAIN}{router.prefix}/reset_password?token={token}"
        }
    )

#Reset Delivery Partner Password
@router.post("/reset_password")
async def reset_password(request: Request, token: str, password: Annotated[str, Form()], service: DeliveryPartnerServiceDep,):
    is_success = await service.reset_password(token, password)
    templates = Jinja2Templates(TEMPLATE_DIR)
    return templates.TemplateResponse(
        request = request,
        name = "password/reset_password_success.html" if is_success else "reset_password_failed.html",
    )

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