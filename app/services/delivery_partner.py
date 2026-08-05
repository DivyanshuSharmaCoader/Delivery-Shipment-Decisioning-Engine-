from app.core.exceptions import DeliveryPartnerNotAvailable
from app.database.models import DeliveryPartner, Shipment, Location
from app.api.schemas.delivery_partner import DeliveryPartnerCreate
from .user import UserService
from sqlmodel import select, any_
from typing import Sequence

class DeliveryPartnerService(UserService):
    def __init__(self, session):
        super().__init__(DeliveryPartner, session)


    async def add(self, delivery_partner: DeliveryPartnerCreate):
        print(delivery_partner.model_dump())
        partner: DeliveryPartner = await self._add_user(
        delivery_partner.model_dump(exclude = {"serviceable_zip_codes"}),
        "partner",
    )
        for zip_code in delivery_partner.serviceable_zip_codes:
            location = await self.session.get(Location, zip_code)
            partner.serviceable_locations.append(
                location
                if location
                else Location(zip_code)
            )
        return await self._update(partner)

  
    async def get_partners_by_zipcode(self, zipcode: int) -> Sequence[DeliveryPartner]:
        return (
            await self.session.scalars(
            select(DeliveryPartner)
            .join(DeliveryPartner.serviceable_locations)
            .where(Location.zip_code == zipcode)
        )
    ).all()

    # async def assign_shipment(self, shipment: Shipment):
    #     print("Shipment destination:", shipment.destination)
    #     eligible_partners= await self.get_partners_by_zipcode(shipment.destination)
    #     print("Eligible partners:", eligible_partners)
    #     for partner in eligible_partners:
    #         print(partner.name, partner.current_handling_capacity)
    #         if partner.current_handling_capacity > 0:
    #             partner.shipments.append(shipment)    
    #             return partner

    #     raise HTTPException(
    #         status_code=status.HTTP_406_NOT_ACCEPTABLE,
    #         detail="no delivery partner available!",
    #     )
    
    async def assign_shipment(self, shipment: Shipment):
        print("Destination =", shipment.destination)
        print("Type =", type(shipment.destination))

        eligible_partners = await self.get_partners_by_zipcode(shipment.destination)

        print("Partners =", eligible_partners)

        for partner in eligible_partners:
            if partner.current_handling_capacity > 0:
                partner.shipments.append(shipment)
                return partner

        raise DeliveryPartnerNotAvailable()

            

    async def update(self, partner: DeliveryPartner):
        return await self._update(partner)

    async def token(self, email, password) -> str:
        return await self._generate_token(email, password)