from pydantic import BaseModel, EmailStr
from pydantic import Field


class BaseDeliveryPartner(BaseModel):
    name: str
    email: EmailStr

    # MUST match DeliveryPartnerService.add()
    serviceable_zip_codes: list[int]

    max_handling_capacity: int


class DeliveryPartnerRead(BaseDeliveryPartner):
    pass


class DeliveryPartnerUpdate(BaseModel):
    serviceable_zip_codes: list[int] | None = Field(default=None)
    max_handling_capacity: int | None = Field(default=None)


class DeliveryPartnerCreate(BaseDeliveryPartner):
    password: str