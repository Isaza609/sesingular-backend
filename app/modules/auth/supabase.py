"""Verificación de tokens emitidos por Supabase Auth (GoTrue).

Orden de verificación:
1. JWKS del proyecto (claves asimétricas, proyectos nuevos) — local, con caché.
2. HS256 con SUPABASE_JWT_SECRET si está configurado (proyectos legacy).
3. Llamada a GoTrue /auth/v1/user como último recurso (con caché corta en memoria).
"""

from __future__ import annotations

import hashlib
import time

import httpx
import jwt
from jwt import PyJWKClient

from app.core.config import get_settings

settings = get_settings()

_jwks_client: PyJWKClient | None = None

# token-hash -> (claims, expira_epoch); evita llamar a GoTrue en cada request
_userinfo_cache: dict[str, tuple[dict, float]] = {}
_USERINFO_TTL = 60.0


class SupabaseAuthError(Exception):
    pass


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        if not settings.supabase_url:
            raise SupabaseAuthError("SUPABASE_URL no configurado")
        _jwks_client = PyJWKClient(
            f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json",
            cache_keys=True,
            lifespan=3600,
        )
    return _jwks_client


def _verify_via_gotrue(token: str) -> dict:
    key = hashlib.sha256(token.encode()).hexdigest()
    cached = _userinfo_cache.get(key)
    now = time.monotonic()
    if cached and cached[1] > now:
        return cached[0]

    # Llamada solo de servidor: la service key nunca sale del backend y evita
    # depender de que la anon key esté bien configurada aquí.
    apikey = settings.supabase_service_role_key or settings.supabase_anon_key
    resp = httpx.get(
        f"{settings.supabase_url.rstrip('/')}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": apikey,
        },
        timeout=10.0,
    )
    if resp.status_code != 200:
        raise SupabaseAuthError(f"GoTrue rechazó el token ({resp.status_code})")
    data = resp.json()
    claims = {"sub": data.get("id"), "email": data.get("email")}
    if not claims["sub"]:
        raise SupabaseAuthError("Respuesta de GoTrue sin id de usuario")

    # Poda simple para que la caché no crezca sin límite
    if len(_userinfo_cache) > 500:
        _userinfo_cache.clear()
    _userinfo_cache[key] = (claims, now + _USERINFO_TTL)
    return claims


def verify_token(token: str) -> dict:
    """Devuelve los claims del token ({sub, email, ...}) o lanza SupabaseAuthError."""
    header = jwt.get_unverified_header(token)
    alg = header.get("alg", "")

    if alg.startswith("HS"):
        if settings.supabase_jwt_secret:
            try:
                return jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    audience="authenticated",
                )
            except jwt.PyJWTError as exc:
                raise SupabaseAuthError(f"Token HS256 inválido: {exc}") from exc
        return _verify_via_gotrue(token)

    # La primera obtención del JWKS puede fallar de forma transitoria: reintentar una vez
    for attempt in (1, 2):
        try:
            signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
            return jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience="authenticated",
            )
        except (jwt.PyJWTError, SupabaseAuthError):
            if attempt == 2:
                return _verify_via_gotrue(token)
