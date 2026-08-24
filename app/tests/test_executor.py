from unittest.mock import MagicMock, patch
import pytest
from app.config import app_settings, notification_settings
from app.worker.executor import execute
from app.worker.tasks import send_email_with_template, send_email_api


@pytest.mark.asyncio
async def test_executor_direct_mode():
    original_mode = app_settings.TASK_EXECUTION_MODE
    try:
        app_settings.TASK_EXECUTION_MODE = "direct"
        
        mock_task = MagicMock()
        mock_task.delay = MagicMock()
        
        await execute(mock_task, "arg1", key="value")
        
        mock_task.assert_called_once_with("arg1", key="value")
        mock_task.delay.assert_not_called()
    finally:
        app_settings.TASK_EXECUTION_MODE = original_mode


@pytest.mark.asyncio
async def test_executor_celery_mode():
    original_mode = app_settings.TASK_EXECUTION_MODE
    try:
        app_settings.TASK_EXECUTION_MODE = "celery"
        
        mock_task = MagicMock()
        mock_task.delay = MagicMock()
        
        await execute(mock_task, "arg1", key="value")
        
        mock_task.delay.assert_called_once_with("arg1", key="value")
        mock_task.assert_not_called()
    finally:
        app_settings.TASK_EXECUTION_MODE = original_mode


def test_send_email_resend_api_mocked():
    notification_settings.SUPPRESS_SEND = 0
    notification_settings.RESEND_API_KEY = "re_test_key_12345"
    notification_settings.MAIL_FROM = "onboarding@resend.dev"
    notification_settings.MAIL_FROM_NAME = "FastShip"

    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "msg_12345"}
    mock_response.raise_for_status.return_value = None

    with patch("httpx.Client.post", return_value=mock_response) as mock_post:
        res = send_email_api(
            recipients=["test@example.com"],
            subject="Verification Test",
            html="<p>Test</p>"
        )
        assert res == {"id": "msg_12345"}
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.resend.com/emails"
        assert kwargs["json"]["to"] == ["test@example.com"]
        assert kwargs["json"]["subject"] == "Verification Test"
        assert kwargs["headers"]["Authorization"] == "Bearer re_test_key_12345"

    notification_settings.SUPPRESS_SEND = 1
