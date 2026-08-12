"""Asset inventory — builds a persistent registry of targets, subdomains, and tech stacks."""

import ipaddress
import logging
from datetime import UTC, datetime
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.adapters.httpx_fingerprint_adapter import HttpxFingerprintRunner
from app.adapters.subfinder_adapter import SubfinderRunner
from app.config import settings
from app.models import Asset, Subdomain

logger = logging.getLogger(__name__)


def _hostname(target: str) -> str:
    parsed = urlparse(target if "://" in target else f"//{target}")
    return parsed.hostname or target


def is_domain(target: str) -> bool:
    """True if target's hostname is a domain name (not a raw IP)."""
    host = _hostname(target)
    try:
        ipaddress.ip_address(host)
        return False
    except ValueError:
        return True


async def run_recon_and_update_asset(target: str, session: AsyncSession) -> dict:
    """Run subdomain enum + tech fingerprinting (fail-open), persist to Asset/Subdomain,
    and return a summary dict for use by the AI orchestrator."""
    host = _hostname(target)
    summary: dict = {"subdomains": [], "tech_stack": []}

    # Upsert Asset row
    stmt = select(Asset).where(Asset.target == host)
    result = await session.execute(stmt)
    asset = result.scalar_one_or_none()
    if not asset:
        asset = Asset(target=host)
        session.add(asset)
        await session.commit()
        await session.refresh(asset)

    asset.last_scanned = datetime.now(UTC)
    asset.scan_count += 1

    discovered: list[str] = []
    if settings.subdomain_enum_enabled and is_domain(target):
        try:
            discovered = await SubfinderRunner().run(host, max_results=settings.max_subdomains_scanned)
        except Exception:
            logger.exception("Subdomain enum failed for %s", host)

    tech_results: list[dict] = []
    if settings.tech_fingerprint_enabled:
        hosts_to_check = [target] + [f"https://{d}" for d in discovered[:settings.max_subdomains_scanned]]
        try:
            tech_results = await HttpxFingerprintRunner().run(hosts_to_check)
        except Exception:
            logger.exception("Tech fingerprint failed for %s", host)

    all_tech: set[str] = set()
    for r in tech_results:
        for t in r.get("tech", []):
            all_tech.add(t)

    # Persist subdomains (skip if already recorded)
    existing_stmt = select(Subdomain.subdomain).where(Subdomain.asset_id == asset.id)
    existing_result = await session.execute(existing_stmt)
    existing_subs = {row[0] for row in existing_result.all()}

    for d in discovered:
        if d in existing_subs:
            continue
        match = next((r for r in tech_results if d in r.get("url", "")), None)
        sub = Subdomain(
            asset_id=asset.id,
            subdomain=d,
            is_alive=bool(match),
            status_code=match.get("status_code") if match else None,
            title=match.get("title") if match else None,
            tech=",".join(match.get("tech", [])) if match else None,
        )
        session.add(sub)

    if all_tech:
        asset.tech_stack = ",".join(sorted(all_tech))
    session.add(asset)
    await session.commit()

    summary["subdomains"] = discovered
    summary["tech_stack"] = sorted(all_tech)
    return summary
