from typing import Annotated
from app.api.tag import APITag
from fastapi import APIRouter, Form, Request, status
from uuid import UUID

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import app_settings
from app.core.exceptions import EntityNotFound, NothingToUpdate
from app.database.models import TagName
from app.utils import TEMPLATE_DIR
from ..dependencies import SessionDep, ShipmentServiceDep, SellerDep, DeliveryPartnerDep
from ..schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentReview, ShipmentUpdate

# api router to group endpoints
router = APIRouter(prefix="/shipment", tags=[APITag.SHIPMENT])

templates = Jinja2Templates(TEMPLATE_DIR)

### Read a shipment by id
@router.get("/", response_model=ShipmentRead)
async def get_shipment(id: UUID, service: ShipmentServiceDep):
    # Check for shipment with given id
    return await service.get(id)


#Tracking details of shipment 
@router.get("/track")
async def get_tracking(request: Request, id: UUID, service: ShipmentServiceDep):
    #Check for shipment with given id
    shipment = await service.get(id)

    context = shipment.model_dump()
    context["status"] = shipment.status
    context["partner"] = shipment.delivery_partner.name
    context["timeline"] = shipment.timeline
    context["timeline"].reverse()

    return templates.TemplateResponse(
        request = request,
        name = "track.html",
        context = context,
    )


### Create a new shipment with content and weight
@router.post(
    "/",
    response_model=ShipmentRead,
    name="Create Shipment",
    description="Submit a new **shipment**",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Shipment created",
            "content": {
                "application/json": {
                    "example": {
                        "id": "e4c7f6b3-8e1d-4a2b-8f3f-5c5b6d7e8f9a",
                        "status": "pending",
                        "delivery_partner": {
                            "id": 1,
                            "name": "DHL"
                        },
                        "tracking_number": "1234567890",
                        "origin": {
                            "address": "123 Main St, City, Country",
                            "postal_code": "12345"
                        },
                        "destination": {
                            "address": "456 Elm St, City, Country",
                            "postal_code": "67890"
                        },
                        "content": "Electronics",
                        "weight": 2.5,
                        "client_contact_email": "customer@example.com",
                        "client_contact_phone": "+911234567890",
                        "created_at": "2026-07-25T10:30:00Z"
                    }
                }
            },
        },
        status.HTTP_406_NOT_ACCEPTABLE: {
            "description": "Delivery partner not available",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Delivery partner not available"
                    }
                }
            },
        },
    },
)


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
        raise NothingToUpdate()
    
    
    return await service.update(id, shipment_update, partner)

#Get all shipments with tag
@router.get("/tagged", response_model = list[ShipmentRead])
async def get_shipments_with_tag(
    tag_name: TagName,
    session: SessionDep,
):
    tag = await tag_name.tag(session)
    return tag.shipments

###Add a tag to a shipment
@router.get("/tag", response_model = ShipmentRead)
async def add_tag_to_shipment(
    id: UUID,
    tag_name: TagName,
    service: ShipmentServiceDep
):
    return await service.add_tag(id, tag_name)

###Remove a tag from a shipment
@router.delete("/tag", response_model = ShipmentRead)
async def remove_tag_from_shipment(
    id: UUID,
    tag_name: TagName,
    service: ShipmentServiceDep
):
    return await service.remove_tag(id, tag_name)

### Cancle a shipment by id
@router.get("/cancle" , response_model = ShipmentRead)
async def cancle_shipment(id: UUID, seller: SellerDep, service: ShipmentServiceDep) -> dict[str, str]:
    # Remove from database
    return await service.cancle(id, seller)


#Submit a Review for a Shipment
@router.get("/review")
async def submit_review_page(
    request: Request,
    token: str,
):
    return templates.TemplateResponse(
        request = request,
        name = "review.html",
        context = {
            "review_url": f"http://{app_settings.APP_DOMAIN}/shipment/review?token={token}"
        }
    )



#Submit a Review for a Shipment
@router.post("/review")
async def submit_review(
    token: str,
    rating: Annotated[int, Form(ge = 1, le = 5)],
    service: ShipmentServiceDep,
    comment: Annotated[str | None, Form()] = None,
):
    review = ShipmentReview(
    rating=rating,
    comment=comment,
)

    await service.rate(token, review)
    return {"detail": "Review Submitted"}