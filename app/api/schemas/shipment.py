from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.database.models import ShipmentEvent, ShipmentStatus, Seller, Tag, TagName


class BaseShipment(BaseModel):
    content: str = Field(max_length = 100)
    weight: float = Field(le=25)
    destination: int = Field(
        description = "instead use location, location zipcode",
        examples = [11001, 11002, 11003, 11004, 11005],
        deprecation=True,
    )

class TagRead(BaseModel):
    name: TagName
    instruction: str 

class ShipmentRead(BaseShipment):
    id: UUID
    timeline: list[ShipmentEvent]
    estimated_delivery: datetime
    tags: list[Tag]


class ShipmentCreate(BaseShipment):
    """Shipment details to create a new shipment"""
    client_contact_email: EmailStr
    client_contact_phone: str | None = Field(default=None)
    

class ShipmentUpdate(BaseModel):
    location: int | None = Field(default = None)
    status: ShipmentStatus | None = Field(default=None)
    verification_code: int | None = Field(default = None)
    discription: str | None = Field(default = None)
    estimated_delivery: datetime | None = Field(default=None)


class ShipmentReview(BaseModel):
    rating: int = Field(ge = 1, le = 5)
    comment: str | None = Field(default = None)