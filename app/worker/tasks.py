import logging
import httpx
import jinja2
from asgiref.sync import async_to_sync
from celery import Celery
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from twilio.rest import Client

from pathlib import Path
from app.config import db_settings, notification_settings
from app.utils import TEMPLATE_DIR

logger = logging.getLogger(__name__)

fastmail = FastMail(
    ConnectionConfig(
        **notification_settings.model_dump(
            exclude=["TWILIO_SID", "TWILIO_AUTH_TOKEN", "TWILIO_NUMBER", "RESEND_API_KEY"]
        ),
        TEMPLATE_FOLDER=TEMPLATE_DIR,
    )
)

twilio_client = Client(
    notification_settings.TWILIO_SID or "AC_dummy",
    notification_settings.TWILIO_AUTH_TOKEN or "dummy_token",
)

_jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_DIR))

send_message = async_to_sync(fastmail.send_message)

app = Celery(
    "api-tasks",
    broker=db_settings.REDIS_URL(9),
    backend=db_settings.REDIS_URL(9),
)


def render_template(template_name: str, context: dict) -> str:
    template = _jinja_env.get_template(template_name)
    return template.render(**context)


def send_email_api(recipients: list[str], subject: str, html: str | None = None, text: str | None = None):
    if notification_settings.SUPPRESS_SEND:
        logger.info(f"SUPPRESS_SEND is enabled. Suppressing email to {recipients}")
        return {"status": "suppressed"}

    api_key = notification_settings.RESEND_API_KEY
    if api_key:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        from_email = notification_settings.MAIL_FROM or "onboarding@resend.dev"
        from_name = notification_settings.MAIL_FROM_NAME or "FastShip"
        sender = f"{from_name} <{from_email}>" if from_name and "<" not in from_email else from_email

        payload = {
            "from": sender,
            "to": recipients,
            "subject": subject,
        }
        if html:
            payload["html"] = html
        if text:
            payload["text"] = text

        with httpx.Client(timeout=10.0) as client:
            response = client.post("https://api.resend.com/emails", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    else:
        # Fallback to FastMail SMTP if RESEND_API_KEY is not set
        subtype = MessageType.html if html else MessageType.plain
        body = html if html else text
        message = MessageSchema(
            recipients=recipients,
            subject=subject,
            body=body,
            subtype=subtype,
        )
        send_message(message)
        return {"status": "sent_via_smtp"}


@app.task
def send_mail(
    recipients: list[str],
    subject: str,
    body: str,
):
    send_email_api(recipients=recipients, subject=subject, text=body)
    return "Message Sent!"


@app.task
def send_email_with_template(
    recipients: list[EmailStr],
    subject: str,
    context: dict,
    template_name: str,
):
    html_content = render_template(template_name, context)
    send_email_api(recipients=recipients, subject=subject, html=html_content)
    return "Message Sent!"


@app.task
def send_sms(to: str, body: str):
    if notification_settings.SUPPRESS_SEND:
        return "Suppressed SMS"
    twilio_client.messages.create(
        from_=notification_settings.TWILIO_NUMBER,
        to=to,
        body=body,
    )


@app.task
def add_log(message: str):
    with open("file.log", "a") as file:
        file.write(message + "\n")