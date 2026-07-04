from pydantic import BaseModel, EmailStr
from pydantic import Field

class BaseDeliveryPartner(BaseModel):
    name: str
    email: EmailStr
    serviceable_zip_code: list[int]
    max_handling_capacity: int

class DeliveryPartnerRead(BaseDeliveryPartner):
    pass

class DeliveryPartnerUpdate(BaseModel):
    serviceable_zip_code: list[int] | None = Field(default = None)
    max_handling_capacity: int | None = Field(default = None)

class DeliveryPartnerCreate(BaseDeliveryPartner):
    password: str