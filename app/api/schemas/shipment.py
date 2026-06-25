from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID
from app.database.models import ShipmentStatus, Seller


class BaseShipment(BaseModel):
    content: str
    weight: float = Field(le=25)
    destination: int


class ShipmentRead(BaseShipment):
    id: UUID
    seller: Seller
    status: ShipmentStatus
    estimated_delivery: datetime


class ShipmentCreate(BaseShipment):
    pass
    

class ShipmentUpdate(BaseModel):
    status: ShipmentStatus | None = Field(default=None)
    estimated_delivery: datetime | None = Field(default=None)