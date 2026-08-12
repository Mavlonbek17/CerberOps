"""Notification delivery — Slack, webhook, and email."""

import json
import logging
import smtplib
from email.mime.text import MIMEText

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def send_slack(webhook_url: str, message: str) -> None:
    """POST a Slack incoming-webhook message."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(webhook_url, json={"text": message})


async def send_webhook(url: str, payload: dict) -> None:
    """POST a generic JSON webhook."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(url, json=payload)


def send_email(to: str, subject: str, body: str) -> None:
    """Send a plain-text email via SMTP (synchronous, run in thread if needed)."""
    if not settings.smtp_host or not to:
        return
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_user:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


async def dispatch_notification(
    notif_type: str,
    config_json: str,
    event: str,
    target: str,
    findings_count: int,
    critical_count: int,
) -> None:
    """Route a notification to the correct delivery channel."""
    try:
        cfg = json.loads(config_json)
        message = (
            f"CerberOps [{event}] — {target}: "
            f"{findings_count} findings ({critical_count} critical)"
        )
        payload: dict = {
            "event": event,
            "target": target,
            "findings_count": findings_count,
            "critical_count": critical_count,
        }
        if notif_type == "slack":
            await send_slack(cfg.get("webhook_url", ""), message)
        elif notif_type == "webhook":
            await send_webhook(cfg.get("url", ""), payload)
        elif notif_type == "email":
            send_email(
                cfg.get("to", settings.notification_email_to),
                f"CerberOps: {event} — {target}",
                message,
            )
    except Exception as exc:
        logger.warning("Notification dispatch failed: %s", exc)
