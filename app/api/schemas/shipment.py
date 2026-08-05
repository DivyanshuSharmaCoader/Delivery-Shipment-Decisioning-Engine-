from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, model_validator
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
    instructions: str


class ShipmentRead(BaseShipment):
    id: UUID
    timeline: list[ShipmentEvent]
    estimated_delivery: datetime
    tags: list[Tag]
    qr_code_url: str | None = None
    pickup_location: int | None = None   # seller's zip_code — where partner picks up from

    @model_validator(mode="before")
    @classmethod
    def populate_pickup_location(cls, data):
        """Populate pickup_location from the related Seller model if not set."""
        if isinstance(data, dict):
            seller = data.get("seller")
            if seller:
                zip_code = getattr(seller, "zip_code", None) or (seller.get("zip_code") if isinstance(seller, dict) else None)
                if zip_code:
                    data["pickup_location"] = zip_code
        else:
            seller = getattr(data, "seller", None)
            if seller:
                zip_code = getattr(seller, "zip_code", None)
                if zip_code:
                    try:
                        data.pickup_location = zip_code
                    except AttributeError:
                        if hasattr(data, "__dict__"):
                            data.__dict__["pickup_location"] = zip_code
        return data



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