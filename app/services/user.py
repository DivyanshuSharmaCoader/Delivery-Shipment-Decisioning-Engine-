from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import BadCredentials, ClientNotVerified, InvalidToken, BadPassword
from app.database.models import User
from app.worker.tasks import send_email_with_template
from .base import BaseService
from sqlalchemy import select
from passlib.context import CryptContext 
from app.utils import decode_url_safe_token, generate_access_token, generate_url_safe_token
from app.config import app_settings
from passlib.exc import PasswordValueError

password_context=CryptContext(schemes=["bcrypt"])

class UserService(BaseService):
    def __init__(self, model: User, session: AsyncSession):
        self.model = model
        self.session = session

    async def _add_user(self, data: dict, router_prefix: str):
        try:
            user = self.model(
                **data,
                password_hash=password_context.hash(data["password"]),
            )
        except PasswordValueError:
            raise BadPassword()

        user = await self._add(user)
        token = generate_url_safe_token({
            "email": user.email,
            "id": str(user.id)
        })
        send_email_with_template.delay(
            recipients = [user.email],
            subject="verify your account with FastShip",
            context={
                "username": user.name,
                "verification_url": f"{app_settings.APP_DOMAIN}/{router_prefix}/verify?token={token}"
            },
            template_name="mail_email_verify.html",
        )
        return user
    
    async def verify_email(self, token: str):
        token_data = decode_url_safe_token(token)
        if not token_data:
            raise InvalidToken()
        user = await self._get(UUID(token_data["id"]))
        user.email_verified = True
        await self._update(user)


    async def _get_by_email(self, email) -> User|None:
        return await self.session.scalar(
            select(self.model).where(self.model.email == email)
        )

    async def _generate_token(self, email, password) -> str:
        user = await self._get_by_email(email)
        if user is None or not password_context.verify(password, user.password_hash,):
            raise BadCredentials()
        if not user.email_verified:
            raise ClientNotVerified()

        return generate_access_token(
            data={
                "user": {
                    "name": user.name,
                    "id": str(user.id),
                }
            }
        )

    async def send_password_reset_link(self, email, router_prefix):
        user = await self._get_by_email(email)
        token = generate_url_safe_token({"id": str(user.id)}, salt="password_reset")

        send_email_with_template.delay(
            recipients=[user.email],
            subject = "Fastship Account Password Reset",
            context = {
                "username": user.name,
                "reset_url": f"http://{app_settings.APP_DOMAIN}{router_prefix}/reset_password_form?token={token}"
            },
            template_name="mail_password_reset.html",
        )

    async def reset_password(self, token: str, password: str) -> bool:
        print("TOKEN:", token)
        token_data = decode_url_safe_token(
            token,
            salt="password_reset",
            expiry=timedelta(days=1),
        )
        print("TOKEN DATA:", token_data)
        if not token_data:
            return False
        user = await self._get(UUID(token_data["id"]))
        user.password_hash = password_context.hash(password)
        await self._update(user)
        return True