import pytest

from app.core.database import reset_database
from app.seed.demo_data import seed_demo_data


@pytest.fixture(autouse=True)
def reset_in_memory_database():
    reset_database()
    seed_demo_data()
    yield
    reset_database()
