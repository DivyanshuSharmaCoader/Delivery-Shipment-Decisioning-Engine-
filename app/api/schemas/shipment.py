from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from app.database.models import ShipmentEvent, ShipmentStatus, Seller


class BaseShipment(BaseModel):
    content: str
    weight: float = Field(le=25)
    destination: int


class ShipmentRead(BaseShipment):
    id: UUID
    timeline: list[ShipmentEvent]
    estimated_delivery: datetime


class ShipmentCreate(BaseShipment):
    client_contact_email: EmailStr
    client_contact_phone: int | None = Field(default=None)
    

class ShipmentUpdate(BaseModel):
    location: int | None = Field(default = None)
    status: ShipmentStatus | None = Field(default=None)
    discription: str | None = Field(default = None)
    estimated_delivery: datetime | None = Field(default=None)