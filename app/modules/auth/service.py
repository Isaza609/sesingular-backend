from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import status

from app.core.config import get_settings


class AuthServiceError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_502_BAD_GATEWAY) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


@dataclass
class SupabaseAuthService:
    supabase_url: str
    anon_key: str
    service_role_key: str

    @classmethod
    def from_settings(cls) -> "SupabaseAuthService":
        settings = get_settings()
        return cls(
            supabase_url=settings.supabase_url.rstrip("/"),
            anon_key=settings.supabase_anon_key,
            service_role_key=settings.supabase_service_role_key,
        )

    def _require_config(self, admin: bool = False) -> None:
        if not self.supabase_url or not self.anon_key:
            raise AuthServiceError("Supabase Auth no esta configurado")
        if admin and not self.service_role_key:
            raise AuthServiceError("Supabase service role key no esta configurada")

    def _headers(self, admin: bool = False, bearer: str | None = None) -> dict[str, str]:
        key = self.service_role_key if admin else self.anon_key
        headers = {"apikey": key, "Content-Type": "application/json"}
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        elif admin:
            headers["Authorization"] = f"Bearer {self.service_role_key}"
        return headers

    def _request(self, method: str, path: str, *, admin: bool = False, bearer: str | None = None, **kwargs: Any) -> dict:
        self._require_config(admin=admin)
        try:
            response = httpx.request(
                method,
                f"{self.supabase_url}{path}",
                headers=self._headers(admin=admin, bearer=bearer),
                timeout=15.0,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise AuthServiceError("No se pudo contactar Supabase Auth") from exc
        if response.status_code >= 400:
            detail = _supabase_error_message(response)
            if response.status_code in (400, 401):
                raise AuthServiceError(detail or "Credenciales invalidas", status.HTTP_401_UNAUTHORIZED)
            if response.status_code == 422:
                raise AuthServiceError(detail or "Datos invalidos", status.HTTP_422_UNPROCESSABLE_ENTITY)
            raise AuthServiceError(detail or "Supabase Auth rechazo la operacion", response.status_code)
        if not response.content:
            return {}
        return response.json()

    def sign_up_buyer(self, email: str, password: str, metadata: dict) -> dict:
        return self._request(
            "POST",
            "/auth/v1/signup",
            json={"email": email, "password": password, "data": {**metadata, "role": "buyer"}},
        )

    def sign_in_with_password(self, email: str, password: str) -> dict:
        return self._request(
            "POST",
            "/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
        )

    def send_password_recovery(self, email: str) -> dict:
        return self._request("POST", "/auth/v1/recover", json={"email": email})

    def update_user_password(self, bearer_token: str, new_password: str) -> dict:
        return self._request("PUT", "/auth/v1/user", bearer=bearer_token, json={"password": new_password})

    def admin_create_user(self, email: str, temporary_password: str, metadata: dict) -> dict:
        return self._request(
            "POST",
            "/auth/v1/admin/users",
            admin=True,
            json={
                "email": email,
                "password": temporary_password,
                "email_confirm": True,
                "user_metadata": metadata,
            },
        )

    def admin_update_user_password(self, user_id: str, temporary_password: str) -> dict:
        return self._request(
            "PUT",
            f"/auth/v1/admin/users/{user_id}",
            admin=True,
            json={"password": temporary_password},
        )


def _supabase_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text
    for key in ("msg", "message", "error_description", "error"):
        value = data.get(key)
        if value:
            return str(value)
    return ""


def get_auth_service() -> SupabaseAuthService:
    return SupabaseAuthService.from_settings()
