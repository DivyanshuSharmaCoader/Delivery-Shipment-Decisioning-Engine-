from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from app.api.schemas.seller import SellerCreate
from app.database.models import Seller
from sqlalchemy import select
from fastapi import HTTPException, status
import jwt
from datetime import datetime, timedelta
from app.config import security_settings
from app.utils import generate_access_token


password_context=CryptContext(schemes=["bcrypt"])

class SellerService:
    def __init__(self, session: AsyncSession):
        # Get database session to perform database operations
        self.session = session

    async def add(self, credentials: SellerCreate) -> Seller:
        seller= Seller(
            **credentials.model_dump(exclude={"password"}),
            password_hash= password_context.hash(credentials.password),
        )
        self.session.add(seller)
        await self.session.commit()
        await self.session.refresh(seller)
        return seller

    async def token(self, email, password) -> str:
        return await self._generate_token(email, password)