import pytest
from uuid import UUID
from typing import Any, Dict
from google.oauth2.credentials import Credentials

from google_auth_Manager import AuthManager
from conftest import DummyFlow


def test_get_token():
    token = AuthManager().get_token("statusest@example.com")
    assert isinstance(token, dict)
    assert token["email"] == "statusest@example.com"


def test_authenticate_with_existing_token():
    manager = AuthManager(email="test@example.com", scope=["dummy_scope"])
    creds, email = manager.authenticate()
    assert email == "test@example.com"
    assert creds.valid


def test_authenticate_with_new_credentials(monkeypatch):
    monkeypatch.setattr("google_auth_Manager.os.path.exists", lambda path: True)
    monkeypatch.setattr(
        "google_auth_Manager.InstalledAppFlow.from_client_secrets_file",
        lambda path, scopes: DummyFlow(),
    )

    manager = AuthManager(credential_path="dummy.json", scope=["dummy_scope"])
    creds, email = manager.authenticate()
    assert email == "test@example.com"
    assert creds.valid


def test_authenticate_with_missing_scope():
    manager = AuthManager(email="test@example.com")
    with pytest.raises(ValueError, match="scope cannot be None"):
        manager.authenticate()


def test_authenticate_already_authenticated(monkeypatch_auth):
    with pytest.raises(ValueError, match="User already authenticated"):
        AuthManager(
            email="test@example.com",
            credential_path="dummy.json",
            scope=["dummy_scope"],
        ).authenticate()
