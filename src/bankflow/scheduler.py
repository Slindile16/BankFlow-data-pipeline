"""Run the BankFlow pipeline on a configurable daily schedule."""

import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler

from bankflow.logging_config import configure_logging
from bankflow.pipeline import main as run_pipeline

logger = logging.getLogger(__name__)


def main():
    """Schedule a daily pipeline run (defaults to 02:00 UTC)."""
    configure_logging(os.getenv("BANKFLOW_LOG_FILE"))
    hour = int(os.getenv("BANKFLOW_SCHEDULE_HOUR", "2"))
    minute = int(os.getenv("BANKFLOW_SCHEDULE_MINUTE", "0"))
    timezone = os.getenv("BANKFLOW_SCHEDULE_TIMEZONE", "UTC")
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("Schedule hour must be 0-23 and minute must be 0-59")

    scheduler = BlockingScheduler(timezone=timezone)
    scheduler.add_job(
        run_pipeline,
        trigger="cron",
        hour=hour,
        minute=minute,
        id="bankflow-daily-pipeline",
        name="BankFlow daily pipeline",
        coalesce=True,
        max_instances=1,
        misfire_grace_time=3600,
    )
    logger.info("Scheduling daily pipeline at %02d:%02d (%s)", hour, minute, timezone)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
