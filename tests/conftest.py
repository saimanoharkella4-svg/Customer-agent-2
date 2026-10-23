import os
import pytest

TEST_TOKEN = "test_secret_agent_token_123"

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("AGENT_API_TOKEN", TEST_TOKEN)
    monkeypatch.setenv("TARGET_ENV", "sandbox")
    os.environ["AGENT_API_TOKEN"] = TEST_TOKEN
    os.environ["TARGET_ENV"] = "sandbox"
