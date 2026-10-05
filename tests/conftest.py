import pytest
from fastapi.testclient import TestClient

import app.core.rate_limit as rate_limit_mod
from app.main import app

DEMO1_EMAIL = "demo1@example.com"
DEMO2_EMAIL = "demo2@example.com"
DEMO_PASSWORD = "DemoPass123!"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    # The limiter's counters are process-wide, so one test's /chat calls
    # would otherwise bleed into the next test's rate-limit budget.
    rate_limit_mod._request_times.clear()
    yield
    rate_limit_mod._request_times.clear()


def _login(client, email: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": DEMO_PASSWORD})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def demo1_token(client):
    return _login(client, DEMO1_EMAIL)


@pytest.fixture
def demo2_token(client):
    return _login(client, DEMO2_EMAIL)
