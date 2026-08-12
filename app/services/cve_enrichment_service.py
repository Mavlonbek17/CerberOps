"""CVE enrichment — fetches descriptions/CVSS from NVD and exploit probability from EPSS.
Every lookup is cached in the cve_enrichment table so repeat scans never re-fetch.

Note: this module uses the Python `httpx` pip package (async HTTP client),
not the ProjectDiscovery `httpx` CLI binary used by httpx_fingerprint_adapter.py.
"""

import asyncio
import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.config import settings
from app.models import CveEnrichment

logger = logging.getLogger(__name__)

_NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
_EPSS_URL = "https://api.first.org/data/v1/epss"
_last_nvd_call = 0.0
_NVD_MIN_INTERVAL = 6.0  # seconds — stay under the 5-req/30s public rate limit


async def _throttle() -> None:
    global _last_nvd_call
    now = asyncio.get_event_loop().time()
    wait = _NVD_MIN_INTERVAL - (now - _last_nvd_call)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_nvd_call = asyncio.get_event_loop().time()


async def enrich_cve(cve_id: str, session: AsyncSession) -> CveEnrichment | None:
    """Return cached enrichment, or fetch from NVD + EPSS and cache it."""
    if not settings.cve_enrichment_enabled:
        return None

    stmt = select(CveEnrichment).where(CveEnrichment.cve_id == cve_id)
    result = await session.execute(stmt)
    cached = result.scalar_one_or_none()
    if cached:
        return cached

    description = ""
    cvss_score = None
    cvss_vector = None
    published = None
    refs: list[str] = []

    try:
        await _throttle()
        headers = {"apiKey": settings.nvd_api_key} if settings.nvd_api_key else {}
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(_NVD_URL, params={"cveId": cve_id}, headers=headers)
            if r.status_code == 200:
                data = r.json()
                vulns = data.get("vulnerabilities", [])
                if vulns:
                    cve_data = vulns[0].get("cve", {})
                    descs = cve_data.get("descriptions", [])
                    description = next((d["value"] for d in descs if d.get("lang") == "en"), "")
                    published = cve_data.get("published")
                    metrics = cve_data.get("metrics", {})
                    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
                        if key in metrics and metrics[key]:
                            cvss_data = metrics[key][0].get("cvssData", {})
                            cvss_score = cvss_data.get("baseScore")
                            cvss_vector = cvss_data.get("vectorString")
                            break
                    refs = [ref.get("url", "") for ref in cve_data.get("references", [])][:10]
    except Exception:
        logger.warning("NVD lookup failed for %s", cve_id)

    epss_score = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(_EPSS_URL, params={"cve": cve_id})
            if r.status_code == 200:
                data = r.json().get("data", [])
                if data:
                    epss_score = float(data[0].get("epss", 0))
    except Exception:
        logger.warning("EPSS lookup failed for %s", cve_id)

    enrichment = CveEnrichment(
        cve_id=cve_id,
        description=description or "No description available.",
        cvss_score=cvss_score,
        cvss_vector=cvss_vector,
        epss_score=epss_score,
        published_date=published,
        reference_urls="\n".join(refs) if refs else None,
        fetched_at=datetime.now(UTC),
    )
    session.add(enrichment)
    try:
        await session.commit()
    except Exception:
        await session.rollback()
    return enrichment
