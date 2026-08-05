from datetime import datetime
from enum import Enum
from pydantic import EmailStr
from sqlmodel import Field, SQLModel, Relationship, select
from uuid import uuid4, UUID
from sqlalchemy.dialects import postgresql
from sqlmodel import Column
from sqlalchemy import ARRAY, INTEGER, BigInteger
from sqlalchemy.ext.asyncio import AsyncSession

class TagName(str, Enum):
    EXPRESS = "express"
    STANDARD = "standard"
    FRAGILE = "fragile"
    HEAVY = "heavy"
    INTERNATIONAL = "international"
    DOMESTIC = "domestic"
    TEMPERATURE_CONTROLLED = "temprature_controlled"
    GIFT = "gift"
    RETURN = "return"
    DOCUMENTS = "documents"

    async def tag(self, session: AsyncSession):
        return await session.scalar(
            select(Tag).where(Tag.name == self.value)
        )



class ShipmentStatus(str, Enum):
    placed = "placed"
    in_transit = "in_transit"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    cancelled = "cancelled"

class ShipmentTag(SQLModel, table = True):
    __tablename__ = "shipment_tag"
    shipment_id: UUID = Field(
        foreign_key="shipment.id",
        primary_key=True,
    )
    tag_id: UUID = Field(
        foreign_key="tag.id",
        primary_key=True,
    )


class Tag(SQLModel, table = True):
    __tablename__ = "tag"

    id: UUID = Field(
            sa_column=Column(
                postgresql.UUID,
                default=uuid4,
                primary_key=True,
        )
    )

    name: TagName
    instructions: str

    shipments: list["Shipment"] = Relationship(
        back_populates="tags",
        link_model=ShipmentTag,
        sa_relationship_kwargs={"lazy": "immediate"},
    )


class Shipment(SQLModel, table = True):
    __tablename__ = "shipment"

    id: UUID = Field(
    sa_column=Column(
        postgresql.UUID,
        default=uuid4,
        primary_key=True,
    )
)

    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )

    client_contact_email: EmailStr
    client_contact_phone: str | None

    content: str
    weight: float = Field(le=25)
    destination: int
    estimated_delivery: datetime
    timeline: list["ShipmentEvent"] = Relationship(
        back_populates="shipment",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    seller_id: UUID = Field(foreign_key="seller.id")
    seller: "Seller" = Relationship(
        back_populates="shipments",
        sa_relationship_kwargs={"lazy": "selectin"},
        )

    delivery_partner_id: UUID | None = Field(
        default=None,
        foreign_key="delivery_partner.id",
    )
    delivery_partner: "DeliveryPartner" = Relationship(
        back_populates="shipments",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    review: "Review" = Relationship(
        back_populates = "shipment",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    tags: list[Tag] = Relationship(
        back_populates="shipments",
        link_model=ShipmentTag,
        sa_relationship_kwargs={"lazy": "immediate"},
    )

    @property
    def status(self):
        return self.timeline[-1].status if len(self.timeline) > 0 else None

    @property
    def qr_code_url(self) -> str:
        return f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={self.id}"

    @property
    def pickup_location(self) -> int | None:
        return self.seller.zip_code if self.seller else None

    

class ShipmentEvent(SQLModel, table=True):
    __tablename__="shipment_event"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    
    location: int
    status: ShipmentStatus
    discription: str | None = Field(default = None)
    shipment_id: UUID = Field(foreign_key = "shipment.id")
    shipment: Shipment = Relationship(
        back_populates= "timeline",
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @property
    def description(self) -> str | None:
        """Alias for discription (backwards-compatible field name for API responses)"""
        return self.discription




class User(SQLModel):
    name: str
    email: EmailStr
    email_verified: bool = Field(default = False)
    password_hash: str = Field(exclude=True)

class Seller(User, table= True):
    __tablename__="seller"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )

    address: str | None = Field(default=None)
    zip_code: int | None = Field(default=None)

    shipments: list[Shipment] = Relationship(
        back_populates="seller",
        sa_relationship_kwargs={"lazy": "selectin"},
        )

class ServiceableLocation(SQLModel, table=True):
    __tablename__ = "serviceable_location"

    partner_id: UUID = Field(
        foreign_key="delivery_partner.id",
        primary_key=True,
    )

    location_id: int = Field(
        foreign_key="location.zip_code",
        primary_key=True,
    )

class DeliveryPartner(User, table=True):
    __tablename__="delivery_partner"
    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )

    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )

    # serviceable_zip_code: list[int] = Field(
    #     sa_column=Column(ARRAY(INTEGER)),
    # )

    serviceable_locations: list["Location"] = Relationship(
        back_populates="delivery_partners",
        link_model=ServiceableLocation,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    max_handling_capacity: int
    shipments: list[Shipment] = Relationship(
        back_populates="delivery_partner",
        sa_relationship_kwargs={"lazy": "selectin"},
    )


    @property
    def active_shipments(self):
        return [
            shipment
            for shipment in self.shipments
            if shipment.status != ShipmentStatus.delivered
            and shipment.status != ShipmentStatus.cancelled
        ]

    @property
    def current_handling_capacity(self):
        return self.max_handling_capacity - len(self.active_shipments)

    @property
    def serviceable_zip_codes(self) -> list[int]:
        return [loc.zip_code for loc in self.serviceable_locations]



class Location(SQLModel, table=True):
    __tablename__ = "location"

    zip_code: int = Field(primary_key=True)

    # Additional metadata fields
    # estimated_delivery_days: int = Field(default=3)
    # surcharge: float = Field(default=0.0)
    # active: bool = Field(default=True)

    delivery_partners: list[DeliveryPartner] = Relationship(
        back_populates="serviceable_locations",
        link_model=ServiceableLocation,
        sa_relationship_kwargs={"lazy": "selectin"},
    )        

class Review(SQLModel, table = True):
    __tablename__ = "review"
    id: UUID = Field(
            sa_column=Column(
                postgresql.UUID,
                default=uuid4,
                primary_key=True,
            )
        )
    
    created_at: datetime = Field(
            sa_column=Column(
                postgresql.TIMESTAMP,
                default=datetime.now,
            )
        )
    rating: int = Field(ge = 1, le = 5)
    comment: str | None = Field(default = None)
    shipment_id: UUID = Field(foreign_key="shipment.id")
    shipment: Shipment = Relationship(
        back_populates = "review",
        sa_relationship_kwargs={"lazy": "selectin"},
    )