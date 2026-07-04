import asyncio

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.config import notification_settings

fastmail = FastMail(
    ConnectionConfig(
        **notification_settings.model_dump(),
    )
)

async def send_message():
    await fastmail.send_message(
        message = MessageSchema(
            recipients=["divyasharma1b18@gmail.com"],
            subject="Your Email Delivered With FastShip",
            body = "Things are about to get interesting...",
            subtype=MessageType.plain,
        )
    )
    print("Email Sent!")

asyncio.run(send_message())