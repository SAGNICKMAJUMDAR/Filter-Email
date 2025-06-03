import pytest
import json


class DummyCredentials:
    def __init__(self):
        self.valid = True
        self.expired = False
        self.refresh_token = "dummy_refresh_token"

    def refresh(self, request):
        self.valid = True


class DummyToken:
    def to_dict(self):
        return {
            "token_data": json.dumps(
                {"token": "dummy", "token_uri": "token_uri", "scopes": ["some_scope"]}
            ),
            "email": "statusest@example.com",
        }


class DummyAuthStore:
    def __init__(self, session):
        pass

    def get_token(self, email):
        return DummyToken()

    def get_token_by_id(self, id):
        return DummyToken()

    def save_token(self, email, path, creds):
        pass

    def update_token(self, email, path, creds):
        pass


class DummyDbSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class DummyFlow:
    def run_local_server(self, port=0):
        return DummyCredentials()


@pytest.fixture(autouse=True)
def monkeypatch_auth(monkeypatch):
    monkeypatch.setattr("google_auth_Manager.AuthStore", DummyAuthStore)
    monkeypatch.setattr("google_auth_Manager.get_db_session", lambda: DummyDbSession())
    monkeypatch.setattr(
        "google_auth_Manager.Credentials.from_authorized_user_info",
        lambda data, scope: DummyCredentials(),
    )
    monkeypatch.setattr(
        "google_auth_Manager.get_user_email", lambda creds: "test@example.com"
    )
