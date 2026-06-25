# 57-App: FastAPI Shipment Tracking API

This document provides a comprehensive overview of the application architecture, how data flows through the system, why each file is structured the way it is, and a complete line-by-line breakdown of the code to help you master this codebase.

---

## 1. Overall Flow & Architecture

This application follows a classic **Layered Architecture**. By breaking the application into specific folders (`api/`, `database/`, `services/`), it forces a clean separation of concerns. This means HTTP requests don't mix with database queries, and business logic is kept isolated.

### How Data Flows Through the System
Imagine a user wants to create a new shipment by sending a `POST` request with JSON data. This is exactly what happens:

1. **The Entry Point:** The web server receives the request, and `app/main.py` pushes it into your FastAPI application router.
2. **The Router (`app/api/router.py`):** The router catches the request path (`POST /shipment/`) and immediately passes the raw JSON to the schema layer for validation.
3. **The Schema Validation (`app/api/schemas/shipment.py`):** Pydantic intercepts the JSON. It checks if the `weight` is provided and if it's `< 25`. If it passes, it turns the JSON into a Python object (`ShipmentCreate`).
4. **Dependency Injection (`app/api/dependencies.py`):** FastAPI realizes the route needs a database connection (via the `ServiceDep`), so it reaches into `session.py`, grabs a live database session, wraps it in the `ShipmentService`, and hands it back to the router.
5. **The Service (`app/services/shipment.py`):** The router calls `service.add(shipment)`. The service contains the actual "business brains". It calculates an estimated delivery date automatically (current time + 3 days), assigns a `placed` status, and converts the Pydantic schema into an actual SQLModel.
6. **The Database Model (`app/database/models.py`):** The data enters the form of a `Shipment` SQLAlchemy model which represents a physical row in PostgreSQL.
7. **Execution (`app/database/session.py`):** The service pushes the model to PostgreSQL via `session.commit()`.
8. **Completion:** The database generates an `id`, sends the confirmed shipment data back up through the service, to the router, and out to the user as JSON!

---

## 2. Line-by-Line Code Breakdown

Below is a detailed walkthrough of exactly what every line of code does across the application, starting from the foundational setup.

### A. Configuration & Environment
#### `app/config.py`
This file is designed to safely load environment variables (from `.env`) into runtime memory.
* `from pydantic_settings import BaseSettings, SettingsConfigDict`: Imports tools that let Pydantic handle environment variables automatically.
* `class DatabaseSettings(BaseSettings):`: Defines a class that mandates strictly typed parameters. If `POSTGRES_PORT` isn't an integer in `.env`, the app crashes safely.
* `POSTGRES_SERVER... POSTGRES_DB`: The required variables.
* `model_config = SettingsConfigDict(...)`: Tells Pydantic to look specifically in `./.env` for these variables, and ignore empty or extra unmapped variables.
* `@property def POSTGRES_URL(self):`: dynamically creates the full PostgreSQL connection string dynamically using the username, password, host, and port specified above.
* `settings = DatabaseSettings()`: Instantiates the object globally so other files can just import `settings`.

### B. The Database Layer
#### `app/database/models.py`
This file defines what your PostgreSQL tables look like.
* `from datetime import datetime / enum import Enum`: Standard Python types needed for database fields.
* `from sqlmodel import Field, SQLModel`: SQLModel is a framework that combines Pydantic and SQLAlchemy together seamlessly.
* `class ShipmentStatus(str, Enum):`: Creates a rigid set of acceptable statuses. It stops bad data (like "lost") from accidentally entering the status column.
* `class Shipment(SQLModel, table = True):`: The `table=True` tells SQLModel this isn't just a Python data class, this is an actual PostgreSQL table.
* `__tablename__ = "shipment"`: The physical name of the table in the database.
* `id: int = Field(default=None, primary_key=True)`: The database automatically generates this ID.
* `content: str`: A required text column.
* `weight: float = Field(le=25)`: A limit enforcing that weight must be less than or equal to 25.
* `destination: int`: An integer destination zone.
* `status: ShipmentStatus`: Uses the strict Enum established earlier.
* `estimated_delivery: datetime`: Timestamp column.

#### `app/database/session.py`
This file handles the actual network connection to Postgres.
* `engine = create_async_engine(...)`: Creates the core pool of connections. Uses `asyncpg` which is extremely fast and non-blocking. `echo=True` prints the actual SQL queries out in the terminal logs.
* `async def create_db_tables():`: An async function that runs on startup.
* `async with engine.begin() as connection:`: Starts a transaction with the database.
* `from app.database.models import Shipment`: Imports the models locally within the function so SQLModel registers them right before creating the tables.
* `await connection.run_sync(SQLModel.metadata.create_all)`: Creates all tables in Postgres if they do not exist.
* `async def get_session():`: A generator function that creates short-lived database connections to serve API requests in real-time.
* `async_session = sessionmaker(...)`: Configures the rules for how sessions behave. `expire_on_commit=False` allows us to read shipment data even after the SQL transaction commits.
* `yield session`: Temporarily pauses the execution, hands the live connection to FastAPI, and closes it gracefully once the request is entirely done.

### C. Schemas (Data Validation)
#### `app/api/schemas/shipment.py`
Unlike `models.py` which sits at the DB level, schemas sit at the web level. They validate incoming/outgoing JSON.
* `class BaseShipment(BaseModel):`: Base properties shared by everything.
* `class ShipmentRead(BaseShipment):`: Describes what we SEND to users. They receive an `id`, `status` and `estimated_delivery` alongside base properties.
* `class ShipmentCreate(BaseShipment):`: Describes what users SEND to us. Note how the user shouldn't send an `id` or `status` since the system generates those!
* `class ShipmentUpdate(BaseModel):`: Used for the `PATCH` route. Allows fields to be optional (`| None`).

### D. The Service Layer (Business Logic)
#### `app/services/shipment.py`
* `class ShipmentService:`: Groups business operations.
* `def __init__(self, session...):`: Saves the database session inside the object so methods can use it.
* `async def get(self, id: int)`: Looks up a shipment in the DB using its primary key (`self.session.get`).
* `async def add(...)`:
  * Creates a new `Shipment` database model.
  * `**shipment_create.model_dump()`: Dynamically unpacks the JSON dictionary provided by the user.
  * Overrides `status` to equal `placed`, meaning a user cannot fake a `delivered` status on creation.
  * Uses Python's `datetime` math to calculate a 3 day delivery window.
  * `.add()`, `.commit()`, and `.refresh()` saves the object to the database, finalizes it, and fetches the auto-generated `id` back into the Python object.
* `async def update(...)`: Takes partial data (`dict`), updates the existing shipment fields natively via `shipment.sqlmodel_update`, and commits.
* `async def delete(...)`: Looks up the record and runs `session.delete`.

### E. The API Layer
#### `app/api/dependencies.py`
* `SessionDep`: A shortcut annotation. Any endpoint requesting this will trigger `get_session()` automatically and get a live DB session.
* `def get_shipment_service(session: SessionDep):`: This function receives the live session, pushes it into `ShipmentService(session)`, and returns the completed service.
* `ServiceDep`: When a route parameter asks for this, FastAPI runs the entire chain: gets a DB connection -> puts it in the service -> gives the service to the router.

#### `app/api/router.py`
* `router = APIRouter(prefix="/shipment", tags=["Shipment"])`: Creates an isolated routing group all sharing the `/shipment` URL prefix.
* **`@router.get(...)`**: The Read route. Notice it forces the return object to rigidly match the `ShipmentRead` JSON schema.
  * `shipment = await service.get(id)` handles fetching it.
  * `if shipment is None: raise HTTPException(...)`: Throws a 404 cleanly.
* **`@router.post(...)`**: The Create route. Takes `ShipmentCreate` input, delegates creation entirely to `await service.add(shipment)`.
* **`@router.patch(...)`**: The Update route. 
  * `update = shipment_update.model_dump(exclude_none=True)` isolates only fields the user intentionally provided, ignoring fields they left blank.
* **`@router.delete(...)`**: The Delete route. Simply delegates deletion to the service and returns a nice string.

### F. Application Start
#### `app/main.py`
* `@asynccontextmanager def lifespan_handler(app: FastAPI):`: Code here runs once exactly when the server boots. `await create_db_tables()` ensures the database is ready. `yield` tells FastAPI "I'm done setting up, start receiving traffic."
* `app = FastAPI(...)`: Instantiates the global app and binds the lifespan.
* `app.include_router(router)`: Connects all the `/shipment` endpoints from `router.py` to the main web app.
* `@app.get("/scalar"... return get_scalar_api_reference(...)`: Manually provisions the modern Scalar interactive playground on the `/scalar` path so you can test routes easily in your browser using the OpenAPI spec.
