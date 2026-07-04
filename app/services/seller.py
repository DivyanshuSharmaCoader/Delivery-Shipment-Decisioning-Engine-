from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.seller import SellerCreate
from app.database.models import Seller
from sqlalchemy import select
from fastapi import HTTPException, status
import jwt
from datetime import datetime, timedelta
from app.config import security_settings
from app.utils import generate_access_token
from .user import UserService


class SellerService(UserService):
    def __init__(self, session: AsyncSession):
        # Get database session to perform database operations
        super().__init__(Seller, session)

    async def add(self, seller_create: SellerCreate) -> Seller:
        
        return await self._add_user(seller_create.model_dump())

    async def token(self, email, password) -> str:
        return await self._generate_token(email, password)