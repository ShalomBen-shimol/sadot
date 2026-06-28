"""QR-driven on-site intake links.

Generates readable QR codes that point at the public website intake forms so
staff can print/display them and let visitors fill the surrender/adoption forms
on their own device. Endpoints are admin-protected; the encoded URLs are public.
"""
from io import BytesIO
from urllib.parse import urlencode

import qrcode
from fastapi import APIRouter, Query, Response

from app.api.deps import CurrentUser
from app.core.config import settings

router = APIRouter(prefix="/qr", tags=["qr"])


def _site_base() -> str:
    # public_site_url + frontend_base_path = where the Next.js forms actually live
    # (e.g. https://sadot.lavit.io/crm). Both are trimmed of trailing/leading slashes.
    base = settings.public_site_url.rstrip("/")
    prefix = "/" + settings.frontend_base_path.strip("/") if settings.frontend_base_path.strip("/") else ""
    return base + prefix


def _surrender_url() -> str:
    return f"{_site_base()}/surrender?{urlencode({'src': 'qr'})}"


def _adopt_url(dog_id: int | None = None) -> str:
    params: dict[str, str | int] = {"src": "qr"}
    if dog_id is not None:
        params["dog_id"] = dog_id
    return f"{_site_base()}/adopt?{urlencode(params)}"


def _png(url: str) -> Response:
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/links")
def qr_links(_: CurrentUser, dog_id: int | None = Query(default=None)) -> dict[str, str]:
    """Return the URLs encoded by the QR endpoints (handy for the frontend)."""
    return {
        "surrender": _surrender_url(),
        "adopt": _adopt_url(dog_id),
    }


@router.get(
    "/surrender.png",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
def qr_surrender(_: CurrentUser) -> Response:
    """PNG QR code encoding the public surrender form URL."""
    return _png(_surrender_url())


@router.get(
    "/adopt.png",
    responses={200: {"content": {"image/png": {}}}},
    response_class=Response,
)
def qr_adopt(_: CurrentUser, dog_id: int | None = Query(default=None)) -> Response:
    """PNG QR code encoding the public adoption form URL (optionally deep-linked)."""
    return _png(_adopt_url(dog_id))
