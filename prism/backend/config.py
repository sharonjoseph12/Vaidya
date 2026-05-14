"""
PRISM Platform — Configuration Management
Uses Pydantic BaseSettings for type-safe environment variable parsing.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


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
    encryption_key: str = Field(..., description="32-byte AES key, base64-encoded")
    jwt_algorithm: str = "HS256"

    # --- Federated Learning ---
    fl_server_port: int = Field(default=8080, description="Flower FL server port")
    fl_min_clients: int = Field(default=2, description="Minimum FL clients per round")
    fl_dp_epsilon: float = Field(default=1.0, description="Differential privacy epsilon")
    fl_dp_delta: float = Field(default=1e-5, description="Differential privacy delta")

    # --- CORS ---
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "https://prism-health.vercel.app"],
        description="Allowed CORS origins"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton instance
settings = Settings(
    # Provide defaults for development (overridden by .env in production)
    supabase_url="https://placeholder.supabase.co",
    supabase_anon_key="placeholder-anon-key",
    supabase_service_key="placeholder-service-key",
    encryption_key="cGxhY2Vob2xkZXIta2V5LTMyLWJ5dGVzLWxvbmc=",  # placeholder
) if __name__ != "__main__" else None


def get_settings() -> Settings:
    """FastAPI dependency for settings injection."""
    return Settings()
