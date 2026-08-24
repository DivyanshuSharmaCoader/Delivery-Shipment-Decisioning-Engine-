from unittest.mock import MagicMock
import pytest
from app.config import app_settings
from app.worker.executor import execute


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
