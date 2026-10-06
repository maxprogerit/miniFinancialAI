"""API-level tests with the LLM and embeddings mocked."""
import json
import uuid
from types import SimpleNamespace

import app.api.transactions as transactions_api
import app.services.agent as agent_mod
from app.db.database import get_connection


def _function_call(call_id, name, arguments):
    return SimpleNamespace(type="function_call", call_id=call_id, name=name, arguments=json.dumps(arguments))


def _usage(input_tokens, output_tokens):
    return SimpleNamespace(
        input_tokens=input_tokens, output_tokens=output_tokens, total_tokens=input_tokens + output_tokens
    )


def _response(resp_id, calls, usage):
    return SimpleNamespace(id=resp_id, output=calls, usage=usage)


def test_register_then_login(client):
    email = f"api-test-{uuid.uuid4().hex[:8]}@example.com"

    resp = client.post("/auth/register", json={"email": email, "password": "SomePassword123!"})
    assert resp.status_code == 200, resp.text
    assert "access_token" in resp.json()

    resp = client.post("/auth/login", json={"email": email, "password": "SomePassword123!"})
    assert resp.status_code == 200, resp.text

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE email = %s;", (email,))


def test_refresh_issues_a_new_access_token(client):
    email = f"api-test-{uuid.uuid4().hex[:8]}@example.com"
    register_resp = client.post("/auth/register", json={"email": email, "password": "SomePassword123!"})
    refresh_token = register_resp.json()["refresh_token"]

    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200, resp.text
    new_access_token = resp.json()["access_token"]

    # The new access token actually works against a protected endpoint.
    resp = client.get("/transactions", headers={"Authorization": f"Bearer {new_access_token}"})
    assert resp.status_code == 200, resp.text

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE email = %s;", (email,))


def test_refresh_rejects_an_access_token(client):
    email = f"api-test-{uuid.uuid4().hex[:8]}@example.com"
    register_resp = client.post("/auth/register", json={"email": email, "password": "SomePassword123!"})
    access_token = register_resp.json()["access_token"]

    resp = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401, resp.text

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE email = %s;", (email,))


def test_register_weak_password_rejected(client):
    resp = client.post(
        "/auth/register",
        json={"email": "whatever@example.com", "password": "short"},
    )
    assert resp.status_code == 422  # pydantic min_length=8 validation


def test_chat_returns_full_envelope(client, demo1_token, monkeypatch):
    responses = [
        _response("r1", [_function_call("c1", "finish_with_spending_summary", {
            "total": 2420.0, "currency": "EUR", "category": "electronics", "transaction_count": 4,
        })], _usage(100, 20)),
        _response("r2", [], _usage(5, 2)),
    ]
    monkeypatch.setattr(agent_mod.client.responses, "create", lambda **kw: responses.pop(0))

    resp = client.post(
        "/chat",
        json={"message": "How much on electronics?"},
        headers={"Authorization": f"Bearer {demo1_token}"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"]["total"] == 2420.0
    assert body["tool_calls"] == ["finish_with_spending_summary"]
    assert body["sources"] == []
    assert body["usage"] == {
        "input_tokens": 105, "output_tokens": 22, "total_tokens": 127, "cost_usd": None,
    }


def test_chat_knowledge_answer_surfaces_sources(client, demo1_token, monkeypatch):
    responses = [
        _response("r1", [_function_call("c1", "finish_with_knowledge_answer", {
            "answer": "...", "sources": ["emergency_fund"],
        })], _usage(50, 10)),
        _response("r2", [], _usage(2, 1)),
    ]
    monkeypatch.setattr(agent_mod.client.responses, "create", lambda **kw: responses.pop(0))

    resp = client.post(
        "/chat",
        json={"message": "What is an emergency fund?"},
        headers={"Authorization": f"Bearer {demo1_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["sources"] == ["emergency_fund"]


def test_transactions_import_happy_path(client, demo1_token, monkeypatch):
    monkeypatch.setattr(
        transactions_api, "import_transactions_csv",
        lambda text: {"imported": 1, "skipped": 0, "errors": []},
    )

    csv_content = b"merchant,amount,currency,category,transaction_date\nTest,10,EUR,electronics,2026-09-01\n"
    resp = client.post(
        "/transactions/import",
        files={"file": ("x.csv", csv_content, "text/csv")},
        headers={"Authorization": f"Bearer {demo1_token}"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"imported": 1, "skipped": 0, "errors": []}


