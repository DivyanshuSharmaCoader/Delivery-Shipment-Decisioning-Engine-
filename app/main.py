from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI
from scalar_fastapi import get_scalar_api_reference

from app.api.router import master_router
from app.database.session import create_db_tables
from app.services.notification import NotificationSerice

@asynccontextmanager
async def lifespan_handler(app: FastAPI):
    await create_db_tables()
    yield




app = FastAPI(
    # Server start/stop listener
    lifespan=lifespan_handler,
)


app.include_router(master_router)

@app.get("/mail")
async def send_test_mail(tasks: BackgroundTasks):
    tasks.add_task(
        NotificationSerice().send_email,
        recipients=["todd@xmailg.one"],
        subject="Test Mail comming through once",
        body="You should'nt be interested in everybody..."
    )
    return {"detail": "Mail Sent"}

### Scalar API Documentation
@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )
