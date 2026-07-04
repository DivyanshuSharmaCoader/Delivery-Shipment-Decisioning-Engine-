from fastapi import APIRouter, HTTPException, status
from uuid import UUID
from ..dependencies import ShipmentServiceDep, SellerDep, DeliveryPartnerDep
from ..schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate

# api router to group endpoints
router = APIRouter(prefix="/shipment", tags=["Shipment"])


### Read a shipment by id
@router.get("/", response_model=ShipmentRead)
async def get_shipment(id: UUID, _: SellerDep, service: ShipmentServiceDep):
    # Check for shipment with given id
    shipment = await service.get(id)

    if shipment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Given id doesn't exist!",
        )

    return shipment


### Create a new shipment with content and weight
@router.post("/", response_model=ShipmentRead)
async def submit_shipment(
    seller: SellerDep,
    shipment: ShipmentCreate,
    service: ShipmentServiceDep,
):
    return await service.add(shipment, seller)


### Update fields of a shipment
@router.patch("/", response_model=ShipmentRead)
async def update_shipment(
    id: UUID,
    shipment_update: ShipmentUpdate,
    partner: DeliveryPartnerDep,
    service: ShipmentServiceDep,
):
    # Update data with given fields
    update = shipment_update.model_dump(exclude_none=True)

    if not update:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided to update",
        ) 
    
    
    return await service.update(id, shipment_update, partner)


### Cancle a shipment by id
@router.get("/cancle" , response_model = ShipmentRead)
async def cancle_shipment(id: UUID, seller: SellerDep, service: ShipmentServiceDep) -> dict[str, str]:
    # Remove from database
    return await service.cancle(id, seller)

