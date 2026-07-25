"""Almacenamiento de comprobantes de pago en Supabase Storage (bucket privado).

Se usa la service key del backend, de modo que no hace falta configurar políticas
RLS a mano. Los comprobantes son documentos financieros: el bucket es privado y el
acceso se entrega mediante URLs firmadas de vida corta.
"""

from __future__ import annotations

import uuid

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

ALLOWED_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "application/pdf": "pdf",
}

_bucket_ready = False


def storage_enabled() -> bool:
    settings = get_settings()
    return bool(settings.supabase_url and settings.supabase_service_role_key)


def _headers() -> dict[str, str]:
    key = get_settings().supabase_service_role_key
    return {"Authorization": f"Bearer {key}", "apikey": key}


def _base_url() -> str:
    return get_settings().supabase_url.rstrip("/") + "/storage/v1"


def _ensure_bucket() -> None:
    """Crea el bucket privado la primera vez (idempotente)."""
    global _bucket_ready
    if _bucket_ready:
        return
    bucket = get_settings().receipts_bucket
    with httpx.Client(timeout=20) as client:
        existing = client.get(f"{_base_url()}/bucket/{bucket}", headers=_headers())
        if existing.status_code == 200:
            _bucket_ready = True
            return
        created = client.post(
            f"{_base_url()}/bucket",
            headers=_headers(),
            json={"id": bucket, "name": bucket, "public": False},
        )
        # 409 = ya existía (carrera entre procesos)
        if created.status_code not in (200, 201, 409):
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY, f"No se pudo preparar el almacenamiento: {created.text}"
            )
    _bucket_ready = True


def build_receipt_path(store_id: str, order_id: str, extension: str) -> str:
    """Ruta pedida por el requerimiento: comprobantes/{tienda_id}/{pedido_id}/..."""
    return f"{store_id}/{order_id}/{uuid.uuid4().hex}.{extension}"


def upload_receipt(content: bytes, content_type: str, store_id: str, order_id: str) -> str:
    """Sube el comprobante y devuelve la ruta interna guardada en el pago."""
    if not storage_enabled():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "El almacenamiento de comprobantes no está configurado (falta SUPABASE_URL / SERVICE_ROLE_KEY)",
        )
    extension = ALLOWED_TYPES.get((content_type or "").lower())
    if extension is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato no admitido: usa JPG, PNG o PDF")
    max_bytes = get_settings().receipt_max_bytes
    if len(content) > max_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "El comprobante supera los 5 MB")
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo está vacío")

    _ensure_bucket()
    bucket = get_settings().receipts_bucket
    path = build_receipt_path(store_id, order_id, extension)
    with httpx.Client(timeout=60) as client:
        response = client.post(
            f"{_base_url()}/object/{bucket}/{path}",
            headers={**_headers(), "Content-Type": content_type, "x-upsert": "true"},
            content=content,
        )
    if response.status_code not in (200, 201):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"No se pudo subir el comprobante: {response.text}")
    return path


def signed_url(path: str | None, expires_in: int = 3600) -> str | None:
    """URL temporal para que comprador y vendedor puedan ver el comprobante."""
    if not path or not storage_enabled():
        return None
    settings = get_settings()
    bucket = settings.receipts_bucket
    try:
        with httpx.Client(timeout=20) as client:
            response = client.post(
                f"{_base_url()}/object/sign/{bucket}/{path}",
                headers=_headers(),
                json={"expiresIn": expires_in},
            )
        if response.status_code != 200:
            return None
        signed = response.json().get("signedURL") or response.json().get("signedUrl")
        if not signed:
            return None
        return settings.supabase_url.rstrip("/") + "/storage/v1" + signed
    except httpx.HTTPError:
        return None
