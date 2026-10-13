import pytest

from app.core.database import reset_database
from app.seed.demo_data import seed_demo_data


@pytest.fixture(autouse=True)
def reset_in_memory_database(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_KEY", "")
    from app.core.config import get_settings

    get_settings.cache_clear()
    reset_database()
    seed_demo_data()
    yield
    get_settings.cache_clear()
    reset_database()
