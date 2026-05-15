"""
PRISM Platform — Configuration Management
Uses Pydantic BaseSettings for type-safe environment variable parsing.
"""

from pathlib import Path

from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

from backend.utils.encryption_key import canonical_encryption_key_b64

# Only this file is merged into Settings (in addition to process environment).
BACKEND_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    app_name: str = "PRISM API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = Field(default="development", description="development | staging | production")

    # --- Supabase ---
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous (public) key")
    supabase_service_key: str = Field(..., description="Supabase service role key (server only)")

    # --- Redis ---
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    # --- ABDM ---
    abdm_client_id: Optional[str] = Field(default=None, description="ABDM sandbox client ID")
    abdm_client_secret: Optional[str] = Field(default=None, description="ABDM sandbox client secret")
    abdm_base_url: str = Field(
        default="https://dev.abdm.gov.in/gateway",
        description="ABDM gateway base URL"
    )

    # --- Security ---
    encryption_key: str = Field(
        ...,
        description="Raw AES key length 16/24/32 bytes, base64-encoded (use openssl rand -base64 32)",
    )
    jwt_algorithm: str = "HS256"

    @field_validator("encryption_key")
    @classmethod
    def _encryption_key_aes_length(cls, v: str) -> str:
        return canonical_encryption_key_b64(v)

    # --- Federated Learning ---
    fl_server_port: int = Field(default=8080, description="Flower FL server port")
    fl_min_clients: int = Field(default=2, description="Minimum FL clients per round")
    fl_dp_epsilon: float = Field(default=1.0, description="Differential privacy epsilon")
    fl_dp_delta: float = Field(default=1e-5, description="Differential privacy delta")

    # --- CORS ---
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000", "https://prism-health.vercel.app"],
        description="Allowed CORS origins"
    )

    # --- Layer 1 (real multimodal SENSE) ---
    use_real_sense: bool = Field(
        default=True,
        description="Run layer1_sense PRISMSensePipeline on downloaded scan media; falls back to mock on failure",
    )

    allow_demo_hardcode_fallback: bool = Field(
        default=False,
        description="If true, InferenceService may return static DEMO dict on failure when patient/session id contains 'demo'",
    )

    model_config = SettingsConfigDict(
        # Always load backend/.env regardless of process cwd (avoids wrong key when uvicorn starts from repo root).
        env_file=(BACKEND_ENV_FILE,),
        env_file_encoding="utf-8-sig",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Dotenv last so ``prism/backend/.env`` overrides shell / Windows User env (stale ENCRYPTION_KEY)."""
        return (
            init_settings,
            env_settings,
            file_secret_settings,
            dotenv_settings,
        )


# Singleton instance
settings = Settings(
    # Provide defaults for development (overridden by .env in production)
    supabase_url="https://placeholder.supabase.co",
    supabase_anon_key="placeholder-anon-key",
    supabase_service_key="placeholder-service-key",
    # 32 zero bytes, base64 — dev-only; set ENCRYPTION_KEY in .env for real deployments
    encryption_key="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
) if __name__ != "__main__" else None


def get_settings() -> Settings:
    """FastAPI dependency for settings injection."""
    return Settings()
