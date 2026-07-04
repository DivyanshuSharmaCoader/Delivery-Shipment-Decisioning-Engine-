from datetime import datetime, timedelta
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.shipment import ShipmentCreate, ShipmentUpdate
from app.database.models import DeliveryPartner, Shipment, ShipmentStatus, Seller
from app.services.shipment_event import ShipmentEventService
from .delivery_partner import DeliveryPartnerService
from .base import BaseService


class ShipmentService(BaseService):
    def __init__(self, session: AsyncSession, partner_service: DeliveryPartnerService, event_service: ShipmentEventService,):
        super().__init__(Shipment, session)
        self.partner_service=partner_service
        self.event_service = event_service

    # Get a shipment by id 
    async def get(self, id: UUID) -> Shipment | None:
        return await self._get(id)

    # Add a new shipment
    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        print("ShipmentCreate:", shipment_create)
        print("Destination:", shipment_create.destination)
        new_shipment = Shipment(
            **shipment_create.model_dump(),
            status=ShipmentStatus.placed,
            estimated_delivery=datetime.now() + timedelta(days=3),
            seller_id=seller.id,
        )
        partner = await self.partner_service.assign_shipment(new_shipment,)
        new_shipment.delivery_partner_id = partner.id
        shipment = await self._add(new_shipment)
        event = await self.event_service.add(
            shipment = shipment,
            location = seller.zip_code,
            status = ShipmentStatus.placed,
            discription = f"assigned to {partner.name}"
        )
        shipment.timeline.append(event)
        return shipment
        

    # Update an existing shipment
    async def update(self, id: UUID, shipment_update: ShipmentUpdate, partner: DeliveryPartner) -> Shipment:
        shipment = await self.get(id)
        if shipment.delivery_partner_id != partner.id:
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Not authorized", 
        )
        update = shipment_update.model_dump(exclude_none = True)
        if shipment_update.estimated_delivery:
            shipment.estimated_delivery = shipment_update.estimated_delivery
        if len(update) > 1 or not shipment_update.estimated_delivery:
            await self.event_service.add(
                shipment = shipment,
                **update,
            )
        return await self._update(shipment)

    async def cancle(self, id: UUID, seller: Seller) -> Shipment:
        #Validate the seller
        shipment = await self.get(id)
        if shipment.seller_id != seller.id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not Authorised",
            )
        event = await self.event_service.add(
           shipment = shipment,
           status = ShipmentStatus.cancelled
           )
        
        shipment.timeline.append(event)
        return shipment
    



         

    # Delete a shipment
    async def delete(self, id: UUID) -> None:
        await self._delete(await self.get(id))
        await self.session.commit()