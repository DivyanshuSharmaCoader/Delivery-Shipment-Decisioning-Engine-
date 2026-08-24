from fastapi import BackgroundTasks
from pydantic import EmailStr
from twilio.rest import Client

from app.config import notification_settings
from app.worker.tasks import render_template, send_email_api


class NotificationSerice:
    def __init__(self, tasks: BackgroundTasks | None = None):
        self.tasks = tasks
        self.twilio_client = Client(
            notification_settings.TWILIO_SID or "AC_dummy",
            notification_settings.TWILIO_AUTH_TOKEN or "dummy_token",
        )

    async def send_email(
        self,
        recipients: list[EmailStr],
        subject: str,
        body: str,
    ):
        if self.tasks:
            self.tasks.add_task(
                send_email_api,
                recipients=recipients,
                subject=subject,
                text=body,
            )
        else:
            send_email_api(recipients=recipients, subject=subject, text=body)

    async def send_email_with_template(
        self,
        recipients: list[EmailStr],
        subject: str,
        context: dict,
        template_name: str,
    ):
        html_content = render_template(template_name, context)
        if self.tasks:
            self.tasks.add_task(
                send_email_api,
                recipients=recipients,
                subject=subject,
                html=html_content,
            )
        else:
            send_email_api(recipients=recipients, subject=subject, html=html_content)

    async def send_sms(self, to: str, body: str):
        if notification_settings.SUPPRESS_SEND:
            return "Suppressed SMS"
        self.twilio_client.messages.create(
            from_=notification_settings.TWILIO_NUMBER,
            to=to,
            body=body,
        )