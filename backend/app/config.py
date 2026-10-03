from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    AS_OF_DATE: str = "2026-10-18"
    OPEN_PERIOD: str = "2026-09"
    GSTR3B_DUE_DAY: int = 20
    GST_RATE_CUTOVER: str = "2025-09-22"
    PAYMENT_WINDOW_DAYS: int = 180
    PAYMENT_WARN_DAYS: int = 30
    ROUNDING_TOLERANCE: float = 1.00
    APPROVAL_THRESHOLD: float = 50000.0
    UPI_MDR_RATE: float = 0.004
    UPI_MDR_THRESHOLD: float = 2000.0
    UPI_MDR_CAP: float = 300.0
    UPI_MDR_EFFECTIVE: str = "2026-10-15"
    UPI_MDR_EXEMPT_MERCHANT: bool = False
    LLM_PROVIDER: str = "none"
    RANDOM_SEED: int = 42

    model_config = SettingsConfigDict(env_file=".env")

config = Settings()
