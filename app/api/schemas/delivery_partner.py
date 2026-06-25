from pydantic import BaseModel, EmailStr

class BaseDeliveryPartner(BaseModel):
    name: str
    email: EmailStr
    serviceable_zip_code: list[int]
    max_handeling_capacity: int

class DeliveryPartnerRead(BaseDeliveryPartner):
    pass

class DeliveryPartnerUpdate(BaseModel):
    serviceable_zip_code: list[int]
    max_handeling_capacity: int

class DeliveryPartnerCreate(BaseDeliveryPartner):
    password: str