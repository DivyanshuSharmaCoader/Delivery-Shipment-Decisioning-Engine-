from contextlib import asynccontextmanager
from time import perf_counter
from app.worker.tasks import add_log
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from scalar_fastapi import get_scalar_api_reference
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import master_router
from app.core.exceptions import add_exception_handlers
from app.database.session import create_db_tables
from app.services.notification import NotificationSerice
from app.utils import APP_DIR
from app.api.tag import APITag
from uuid import uuid4
from typing import Annotated
from uuid import UUID
from fastapi import Depends
import os

description = """
Delivery Management System for sellers and delivery Agents

Seller
- Submit shipment effortlessly
- Share tracking links with customers

Delivery Agent
- Auto accept shipments
- Track and update shipment status
- Email and SMS notifications
"""



@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    await create_db_tables()
    yield

app = FastAPI(
    # Server start/stop listener
    title = "FastShip",
    description = description,
    lifespan=lifespan_handler,
    docs_url = None,
    redoc_url = None,
    version="0.1.0",
    terms_of_service="https://fastship.com/terms/",
    contact = {
        "name": "FastShip Support",
        "url": "https://fastship.com/support",
        "email": "support@fastship.com",
    },
    openapi_tags=[
        {
            "name": APITag.SHIPMENT,
            "description": "Operations related to shipments",
        },
        {
            "name": APITag.SELLER,
            "description": "Operations related to seller",
        },
        {
            "name": APITag.PARTNER,
            "description": "Operations related to delivery partner",
        },
    ]
)


allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(master_router)

add_exception_handlers(app)

@app.middleware("http")
async def custom_middleware(request: Request, call_next):
    start = perf_counter()
    response: Response = await call_next(request)
    end = perf_counter()
    time_taken = round(end - start, 2)
    add_log.delay(f"{request.method} {request.url} ({response.status_code}) {time_taken} s")
    return response

class UpperResponse(Response):
    def __init__(self, content = None, status_code = 200, headers = None, media_type = None, background = None):
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content):
        content = content.upper()
        return super().render(content)


#custom response
@app.get("/custom", response_class = UpperResponse,)
def get_custom_response():
    return "sample shipment"

@app.get("/custom-new")
def get_new_data():
    return "NEW CUSTOM RESPONSE!"


@app.get("/mail")
async def send_test_mail(tasks: BackgroundTasks):
    tasks.add_task(
        NotificationSerice().send_email,
        recipients=["todd@xmailg.one"],
        subject="Test Mail comming through once",
        body="You should'nt be interested in everybody..."
    )
    return {"detail": "Mail Sent"}

#Example Dependency
def get_id():
    return uuid4()

#Scalar Running Status
@app.get("/")
def read_root(id: Annotated[UUID, Depends(get_id)]):
    return {
        "detail": str(id),
        }

### Scalar API Documentation
@app.get("/docs", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )
