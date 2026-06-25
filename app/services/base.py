from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from sqlmodel import SQLModel


class BaseService:
    def __init__(self, model: SQLModel, session: AsyncSession):
        self.model = model
        self.session = session

    async def _get(self, id: UUID):
        return await self.session.get(self.model, id)

    async def _create(self, entity: SQLModel):
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def _update(self, entity: SQLModel):
        return await