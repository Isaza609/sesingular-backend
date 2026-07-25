from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "singular-api"
    app_port: int = 3001
    api_prefix: str = "api/v1"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "postgresql+psycopg://singular:singular@localhost:5432/singular"
    db_schema: str = "marketplace"

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    # Solo necesario si el proyecto Supabase firma JWT con HS256 (legacy)
    supabase_jwt_secret: str = ""

    # Almacenamiento de comprobantes de pago (Supabase Storage, bucket privado)
    receipts_bucket: str = "comprobantes"
    receipt_max_bytes: int = 5 * 1024 * 1024

    # Notificaciones por correo (Resend). Sin API key, el envío es no-op.
    email_provider: str = "resend"
    resend_api_key: str = ""
    email_from: str = ""

    admin_email: str = ""
    admin_password: str = ""
    seller_email: str = ""
    seller_password: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def model_post_init(self, __context) -> None:
        # Supabase/URI genérica → driver psycopg3 instalado en el proyecto
        if self.database_url.startswith("postgresql://"):
            object.__setattr__(
                self,
                "database_url",
                "postgresql+psycopg://" + self.database_url.removeprefix("postgresql://"),
            )
        elif self.database_url.startswith("postgres://"):
            object.__setattr__(
                self,
                "database_url",
                "postgresql+psycopg://" + self.database_url.removeprefix("postgres://"),
            )

@lru_cache
def get_settings() -> Settings:
    return Settings()
