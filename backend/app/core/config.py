from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    database_url: str
    jwt_secret: str
    access_token_expire_minutes: int = 1440

    storage_dir: str = "/data/uploads"
    max_upload_bytes: int = 8_000_000

    osm_user_agent: str = "CivicSentinel/1.0 (contact: example@example.com)"
    escalation_hours: int = 48

    # Optional SMTP config (for submission notifications)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""

    # Vision config (optional at runtime)
    gemini_api_key: str | None = None
    yolo_weights_path: str = "models/yolov8n.pt"
    yolo_conf_threshold: float = 0.25

    # NLP config (optional at runtime)
    nlp_model_name: str = "google/flan-t5-small"

    # Comma-separated list of supported output languages for prompting/templates.
    default_languages: str = "en"


settings = Settings()

