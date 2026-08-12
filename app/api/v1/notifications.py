"""Notification configuration endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import NotificationConfig
from app.schemas import ErrorResponse, NotificationConfigCreate, NotificationConfigOut
from app.services.notification_service import dispatch_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ── Helpers ───────────────────────────────────────────────────────

def _nc_to_out(nc: NotificationConfig) -> NotificationConfigOut:
    try:
        config_dict: dict = json.loads(nc.config)
    except Exception:
        config_dict = {}
    events = [e.strip() for e in nc.events.split(",") if e.strip()]
    return NotificationConfigOut(
        id=nc.id,
        name=nc.name,
        type=nc.type,
        config=config_dict,
        events=events,
        enabled=nc.enabled,
        created_at=nc.created_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("", response_model=list[NotificationConfigOut])
async def list_notification_configs(
    session: AsyncSession = Depends(get_session),
) -> list[NotificationConfigOut]:
    """List all notification configurations."""
    result = await session.execute(
        select(NotificationConfig).order_by(NotificationConfig.created_at.desc())
    )
    return [_nc_to_out(nc) for nc in result.scalars().all()]


@router.post("", response_model=NotificationConfigOut, status_code=201)
async def create_notification_config(
    body: NotificationConfigCreate,
    session: AsyncSession = Depends(get_session),
) -> NotificationConfigOut:
    """Create a new notification configuration."""
    nc = NotificationConfig(
        name=body.name,
        type=body.type,
        config=json.dumps(body.config),
        events=",".join(body.events),
        enabled=body.enabled,
    )
    session.add(nc)
    await session.commit()
    await session.refresh(nc)
    return _nc_to_out(nc)


@router.delete("/{nc_id}", responses={404: {"model": ErrorResponse}})
async def delete_notification_config(
    nc_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a notification configuration."""
    result = await session.execute(
        select(NotificationConfig).where(NotificationConfig.id == nc_id)
    )
    nc = result.scalar_one_or_none()
    if not nc:
        raise HTTPException(status_code=404, detail=f"Notification config {nc_id} not found")
    await session.delete(nc)
    await session.commit()
    return {"message": f"Notification config {nc_id} deleted"}


@router.post(
    "/{nc_id}/test",
    responses={404: {"model": ErrorResponse}},
)
async def test_notification_config(
    nc_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Send a test notification using the specified config."""
    result = await session.execute(
        select(NotificationConfig).where(NotificationConfig.id == nc_id)
    )
    nc = result.scalar_one_or_none()
    if not nc:
        raise HTTPException(status_code=404, detail=f"Notification config {nc_id} not found")

    await dispatch_notification(
        notif_type=nc.type,
        config_json=nc.config,
        event="test",
        target="cerberops-test",
        findings_count=0,
        critical_count=0,
    )
    return {"message": f"Test notification sent via {nc.type} ({nc.name})"}
