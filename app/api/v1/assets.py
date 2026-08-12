"""Asset inventory endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import Asset, Subdomain
from app.schemas import AssetDetail, AssetSummary, ErrorResponse, SubdomainOut

router = APIRouter(tags=["assets"])


@router.get("/assets", response_model=list[AssetSummary])
async def list_assets(session: AsyncSession = Depends(get_session)) -> list[AssetSummary]:
    result = await session.execute(select(Asset).order_by(Asset.last_scanned.desc()))
    assets = result.scalars().all()

    out = []
    for a in assets:
        sub_count_result = await session.execute(select(Subdomain).where(Subdomain.asset_id == a.id))
        sub_count = len(sub_count_result.scalars().all())
        out.append(AssetSummary(
            id=a.id,
            target=a.target,
            tech_stack=[t.strip() for t in a.tech_stack.split(",") if t.strip()] if a.tech_stack else [],
            subdomain_count=sub_count,
            scan_count=a.scan_count,
            first_seen=a.first_seen,
            last_scanned=a.last_scanned,
        ))
    return out


@router.get("/assets/{asset_id}", response_model=AssetDetail, responses={404: {"model": ErrorResponse}})
async def get_asset(asset_id: str, session: AsyncSession = Depends(get_session)) -> AssetDetail:
    result = await session.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")

    sub_result = await session.execute(select(Subdomain).where(Subdomain.asset_id == asset_id))
    subs = sub_result.scalars().all()

    return AssetDetail(
        id=asset.id,
        target=asset.target,
        tech_stack=[t.strip() for t in asset.tech_stack.split(",") if t.strip()] if asset.tech_stack else [],
        open_ports=[p.strip() for p in asset.open_ports.split(",") if p.strip()] if asset.open_ports else [],
        subdomains=[
            SubdomainOut(
                subdomain=s.subdomain,
                ip_address=s.ip_address,
                is_alive=s.is_alive,
                status_code=s.status_code,
                title=s.title,
                tech=[t.strip() for t in s.tech.split(",") if t.strip()] if s.tech else [],
                discovered_at=s.discovered_at,
            )
            for s in subs
        ],
        scan_count=asset.scan_count,
        first_seen=asset.first_seen,
        last_scanned=asset.last_scanned,
    )
