"""
Task execution abstraction layer.

Provides a single `execute()` function that routes Celery task calls
to either direct in-process execution or Celery worker dispatch,
based on the TASK_EXECUTION_MODE configuration setting.

CURRENT DEPLOYMENT (TASK_EXECUTION_MODE="direct"):
    Tasks run synchronously inside the FastAPI process.
    No Celery worker or Redis broker (DB 9) required.

FUTURE DEPLOYMENT (TASK_EXECUTION_MODE="celery"):
    Tasks are dispatched via .delay() to a Celery worker
    through the Redis broker. Requires a running worker:
        celery -A app.worker.tasks.app worker --loglevel=info
"""

import asyncio
from app.config import app_settings


async def execute(task, *args, **kwargs):
    """Execute a Celery task either directly or via the Celery broker.

    Args:
        task: A Celery @app.task decorated function.
        *args, **kwargs: Arguments forwarded to the task.

    In "direct" mode, calls asyncio.to_thread(task, *args, **kwargs) to run
    the task in a worker thread without blocking the FastAPI event loop.
    In "celery" mode, calls task.delay(*args, **kwargs) via broker.
    """
    if app_settings.TASK_EXECUTION_MODE == "celery":
        return task.delay(*args, **kwargs)
    return await asyncio.to_thread(task, *args, **kwargs)
