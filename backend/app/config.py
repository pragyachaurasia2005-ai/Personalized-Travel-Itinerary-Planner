import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def reload_environment():
    """Reloads .env from project root so changes can take effect without restart."""
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        # Also check .env.local
        local_env = BASE_DIR / ".env.local"
        if local_env.exists():
            load_dotenv(local_env, override=True)

# Initial load
reload_environment()

class Settings:
    PROJECT_NAME: str = "Personalized Travel Itinerary Planner"
    VERSION: str = "1.1.0"
    API_V1_PREFIX: str = "/api"
    
    # Supported Currencies and baseline conversion rates vs USD (1 USD = X Currency)
    CURRENCY_CONFIG = {
        "USD": {"symbol": "$", "rate": 1.0, "name": "US Dollar"},
        "INR": {"symbol": "₹", "rate": 86.5, "name": "Indian Rupee"},
        "EUR": {"symbol": "€", "rate": 0.95, "name": "Euro"},
        "GBP": {"symbol": "£", "rate": 0.81, "name": "British Pound"},
        "JPY": {"symbol": "¥", "rate": 154.0, "name": "Japanese Yen"},
        "CAD": {"symbol": "C$", "rate": 1.42, "name": "Canadian Dollar"},
        "AUD": {"symbol": "A$", "rate": 1.58, "name": "Australian Dollar"},
    }

    @property
    def GEMINI_API_KEY(self) -> str:
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    @property
    def SUPABASE_URL(self) -> str:
        return os.getenv("SUPABASE_URL", "").strip()

    @property
    def SUPABASE_KEY(self) -> str:
        key = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_ANON_KEY", "")).strip()
        return key

    DB_PATH: Path = BASE_DIR / "travel_planner.db"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
