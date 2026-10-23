import os
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
VALID_TOKEN = "test_secret_agent_token_123"
AUTH_HEADER = {"Authorization": f"Bearer {VALID_TOKEN}"}

def test_health_endpoint():
    """Rule 4: /health returns status ok without auth and without calling model."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_chat_auth_missing_header():
    """Rule 4: Missing token gets HTTP 403 with no detail."""
    res = client.post("/chat", json={"input": "Hello"})
    assert res.status_code == 403

def test_chat_auth_wrong_token():
    """Rule 4: Wrong token gets HTTP 403."""
    res = client.post("/chat", json={"input": "Hello"}, headers={"Authorization": "Bearer wrong_token"})
    assert res.status_code == 403

def test_chat_auth_basic_header():
    """Rule 4: Basic header gets HTTP 403."""
    res = client.post("/chat", json={"input": "Hello"}, headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert res.status_code == 403

def test_chat_auth_token_in_query():
    """Rule 4: Token in URL query gets HTTP 403."""
    res = client.post(f"/chat?token={VALID_TOKEN}", json={"input": "Hello"}, headers=AUTH_HEADER)
    assert res.status_code == 403

def test_chat_valid_response_contract():
    """Rule 4: Response fields, types, and finish_reason values."""
    res = client.post("/chat", json={"input": "Hello"}, headers=AUTH_HEADER)
    assert res.status_code == 200
    data = res.json()

    # Required fields
    assert "output" in data
    assert "finish_reason" in data
    assert "trace_id" in data
    assert "steps_taken" in data
    assert "cost_usd" in data
    assert "tool_calls" in data

    # Type validation
    assert isinstance(data["output"], str)
    assert data["finish_reason"] in [
        "complete", "policy_refusal", "max_steps_reached",
        "timeout", "error", "length", "content_filter", "tool_calls"
    ]
    assert isinstance(data["steps_taken"], int)
    assert isinstance(data["cost_usd"], (float, int))
    assert isinstance(data["tool_calls"], list)

    # Valid UUID format
    uuid_obj = uuid.UUID(data["trace_id"])
    assert str(uuid_obj) == data["trace_id"]

def test_chat_new_trace_id_per_request():
    """Rule 4: trace_id is a new UUID for every request."""
    res1 = client.post("/chat", json={"input": "Hello 1"}, headers=AUTH_HEADER)
    res2 = client.post("/chat", json={"input": "Hello 2"}, headers=AUTH_HEADER)
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["trace_id"] != res2.json()["trace_id"]

def test_chat_input_validation_422():
    """Rule 4: Bad input or input exceeding cap gets 422, never 500."""
    # Exceeding 8,000 characters
    long_input = "a" * 8005
    res = client.post("/chat", json={"input": long_input}, headers=AUTH_HEADER)
    assert res.status_code == 422

    # Missing required 'input' field
    res_missing = client.post("/chat", json={"session_id": "only_session"}, headers=AUTH_HEADER)
    assert res_missing.status_code == 422
