"""Lightweight background scheduler for follow-up sweeps.

Phase 1 uses a simple asyncio loop so there is no external broker dependency.
This is intentionally swappable for Celery/RQ later — see run_followup_sweep,
which is the unit of work a real task queue would call.
"""
import asyncio
import contextlib

from sqlmodel import Session

from app.core.database import engine
from app.core.logging import logger
from app.services import ownership as ownership_service

# Sweep interval in seconds (follow-up due dates are day-grained, so hourly is fine).
SWEEP_INTERVAL_SECONDS = 60 * 60


def run_followup_sweep() -> int:
    with Session(engine) as session:
        return ownership_service.run_due_followups(session)


async def _loop():
    while True:
        try:
            run_followup_sweep()
        except Exception as exc:  # noqa: BLE001 - never let the loop die
            logger.warning("[scheduler] follow-up sweep failed: %s", exc)
        await asyncio.sleep(SWEEP_INTERVAL_SECONDS)


def start(app) -> None:
    task = asyncio.create_task(_loop())
    app.state.scheduler_task = task


async def stop(app) -> None:
    task = getattr(app.state, "scheduler_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
