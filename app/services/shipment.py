from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.shipment import ShipmentCreate, ShipmentReview, ShipmentUpdate
from app.core.exceptions import ClientNotAuthorized, EntityNotFound, InvalidToken
from app.database.models import DeliveryPartner, Review, Seller, Shipment, ShipmentStatus, TagName
from app.database.redis import get_shipment_verification_code
from app.services.shipment_event import ShipmentEventService
from app.utils import decode_url_safe_token

from .base import BaseService
from .delivery_partner import DeliveryPartnerService


class ShipmentService(BaseService):
    def __init__(self, session: AsyncSession, partner_service: DeliveryPartnerService, event_service: ShipmentEventService,):
        super().__init__(Shipment, session)
        self.partner_service=partner_service
        self.event_service = event_service

    # Get a shipment by id 
    async def get(self, id: UUID) -> Shipment | None:
        shipment = await self._get(id)
        if not shipment:
                raise EntityNotFound()
        return shipment

    # Add a new shipment
    async def add(self, shipment_create: ShipmentCreate, seller: Seller) -> Shipment:
        print("ShipmentCreate:", shipment_create)
        print("Destination:", shipment_create.destination)
        new_shipment = Shipment(
            **shipment_create.model_dump(),
            estimated_delivery=datetime.now() + timedelta(days=3),
            seller_id=seller.id,
        )
        partner = await self.partner_service.assign_shipment(new_shipment,)
        new_shipment.delivery_partner_id = partner.id
        shipment = await self._add(new_shipment)
        # Use seller zip_code if available, otherwise fall back to shipment destination
        pickup_location = seller.zip_code if seller.zip_code else shipment_create.destination
        event = await self.event_service.add(
            shipment = shipment,
            location = pickup_location,
            status = ShipmentStatus.placed,
            discription = f"assigned to {partner.name}"
        )
        shipment.timeline.append(event)
        return shipment
        

    # Update an existing shipment
    async def update(self, id: UUID, shipment_update: ShipmentUpdate, partner: DeliveryPartner) -> Shipment:
        shipment = await self.get(id)
        if shipment.delivery_partner_id != partner.id:
            raise ClientNotAuthorized()

        if shipment_update.status == ShipmentStatus.delivered:
            code = await get_shipment_verification_code(shipment.id)

            print("Redis:", code)
            print("Request:", shipment_update.verification_code)


            if code != shipment_update.verification_code:
                raise ClientNotAuthorized()

        update = shipment_update.model_dump(
            exclude_none = True,
            exclude = ["verification_code"],
        )
        if shipment_update.estimated_delivery:
            shipment.estimated_delivery = shipment_update.estimated_delivery
        if len(update) > 1 or not shipment_update.estimated_delivery:
            await self.event_service.add(
                shipment = shipment,
                **update,
            )
        return await self._update(shipment)

    async def add_tag(self, id: UUID, tag_name: TagName):
        shipment = await self.get(id)
        shipment.tags.append(await tag_name.tag(self.session))
        return await self._update(shipment)

    async def remove_tag(self, id: UUID, tag_name: TagName):
            shipment = await self.get(id)
            try:
                shipment.tags.remove(await tag_name.tag(self.session))
            except ValueError:
                raise EntityNotFound()
            return await self._update(shipment)

    async def rate(self, token: str, review: ShipmentReview):
        token_data = decode_url_safe_token(token)
        if not token_data:
            raise InvalidToken()
        shipment = await self.get(UUID(token_data["id"]))
        new_review = Review(
            **review.model_dump(),
            shipment_id = shipment.id,
        )
        self.session.add(new_review)
        await self.session.commit()

    async def cancle(self, id: UUID, seller: Seller) -> Shipment:
        #Validate the seller
        shipment = await self.get(id)
        if shipment.seller_id != seller.id:
            raise ClientNotAuthorized()

        # Use seller's zip_code as the cancel-event location (parcel returns to origin)
        pickup_location = shipment.seller.zip_code if shipment.seller and shipment.seller.zip_code else shipment.destination

        # Update delivery destination to seller's location on cancellation
        shipment.destination = pickup_location

        event = await self.event_service.add(
           shipment = shipment,
           status = ShipmentStatus.cancelled,
           location = pickup_location,
           discription = f"cancelled by seller — return to {pickup_location}",
           )

        shipment.timeline.append(event)
        return await self._update(shipment)
    



         

    # Delete a shipment
    async def delete(self, id: UUID) -> None:
        await self._delete(await self.get(id))
        await self.session.commit()