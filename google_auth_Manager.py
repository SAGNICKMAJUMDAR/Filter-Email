from models import UserToken
from session_manager import get_db_session

from google_auth_store import AuthStore
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from typing import Dict, Any

from auth_utility import get_user_email

import json
import os


class AuthManager:

    def __init__(
        self,
        credential_path: str = None,
        email: str = None,
        scope: str = None,
        re_auth: bool = False,
    ):
        "Initialize authentication requirements"

        self.email = email
        self.scope = scope
        self.cred_details = None
        self.re_auth = re_auth

        if email is not None and not self.get_token(email):
            raise ValueError(f"No token details found for user {email}")
        self.credential_path = credential_path

    def get_token(self, email: str) -> UserToken:
        "Fetch token details for a user"
        with get_db_session() as session:
            user_token: Dict[str, Any] = AuthStore(session).get_token(email).to_dict()
        return user_token

    def save_token(self) -> None:
        "Save newly created token details for a user"
        with get_db_session() as session:
            AuthStore(session).save_token(
                self.email, self.credential_path, self.cred_details
            )

    def update_token(self):
        "Update credential details"
        with get_db_session() as session:
            AuthStore(session).update_token(
                self.email, self.credential_path, self.cred_details
            )

    def authenticate(self):
        "Authenticate user email"

        if self.scope is None:
            raise ValueError("scope cannot be None")
        if self.email is None and self.re_auth:
            raise ValueError("Non Existent user cannot be reauthenticated")
        if self.email is not None and self.credential_path is None and self.re_auth:
            raise ValueError("User cannot be reauthenticated without credential file")
        if (
            self.email is not None
            and self.credential_path is not None
            and not self.re_auth
        ):
            raise ValueError(
                "User already authenticated - Please reauthenticate if needed"
            )
        if self.email is not None and self.credential_path is None and not self.re_auth:
            token_details: UserToken = self.get_token(self.email)
            self.cred_details: Credentials = Credentials.from_authorized_user_info(
                json.loads(token_details["token_data"]), self.scope
            )
            if (
                not self.cred_details.valid
                or self.cred_details.expired
                and self.cred_details.refresh_token
            ):
                self.cred_details.refresh(Request())
                self.update_token()
                return self.cred_details

        if self.credential_path is not None and not os.path.exists(
            self.credential_path
        ):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credential_path}"
            )
        if self.credential_path:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credential_path, self.scope
            )
            self.cred_details = flow.run_local_server(port=0)

        if self.email is not None and self.credential_path is not None:
            self.update_token()
        else:
            self.email = get_user_email(self.cred_details)
            self.save_token()
        return self.cred_details
