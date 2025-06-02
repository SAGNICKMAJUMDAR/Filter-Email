from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update
from models import UserToken

from google.oauth2.credentials import Credentials


class AuthStore:
    "Store implementation related to gmail authentication"

    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_token(self, email: str) -> UserToken:
        "Fetch token details"
        return self.db_session.query(UserToken).filter_by(email=email).first()

    def get_token_by_id(self, account_id: UUID) -> UserToken:
        "Fetch token details for a user"
        return self.db_session.query(UserToken).filter_by(id=account_id).first()

    def save_token(
        self, email: str, credential_path: str, cred_details: Credentials
    ) -> None:
        "Store token details"
        query = (
            insert(UserToken)
            .values(
                email=email,
                credential_path=credential_path,
                token_data=cred_details.to_json(),
            )
            .on_conflict_do_nothing(index_elements=["email"])
        )
        self.db_session.execute(query)

    def update_token(
        self, email: str, credential_path: str, cred_details: Credentials
    ) -> None:
        "Update credential path and token"
        update_data = {}
        if credential_path is not None:
            update_data["credential_path"] = credential_path
        if cred_details is not None:
            update_data["token_data"] = cred_details.to_json()
        if update_data:
            query = (
                update(UserToken).where(UserToken.email == email).values(**update_data)
            )
            self.db_session.execute(query)
