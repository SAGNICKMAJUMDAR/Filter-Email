from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import Optional, List, Dict
import json
from sqlalchemy.exc import SQLAlchemyError

from session_manager import get_db_session
from models import UserToken

from email_storage_service import EmailStorageService, FullMessage
from google_auth_Manager import AuthManager
from auth_utility import get_user_email


class EmailFetcherService:
    def __init__(self, cred_details: Credentials):
        self.cred_details = cred_details
        self.service = build("gmail", "v1", credentials=cred_details)
        self.user_id = "me"
        self.next_page_token: Optional[str] = None

    def _build_query(
        self,
        subject: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        has_attachment: bool = False,
        is_unread: Optional[bool] = None,
        keywords: Optional[List[str]] = None,
    ) -> str:
        filters = {
            "subject": f'"{subject}"' if subject else None,
            "after": after,
            "before": before,
            "has": "attachment" if has_attachment else None,
            "is": "unread" if is_unread else ("read" if is_unread is False else None),
        }
        parts = [f"{k}:{v}" for k, v in filters.items() if v]
        if keywords:
            parts.extend(keywords)
        return " ".join(parts)

    def fetch_emails(
        self,
        max_results: int = 10,
        labels: Optional[List[str]] = None,
        subject: Optional[str] = None,
        after: Optional[str] = None,
        before: Optional[str] = None,
        has_attachment: bool = False,
        is_unread: Optional[bool] = None,
        keywords: Optional[List[str]] = None,
        page_token: Optional[str] = None,
    ) -> Dict:
        query = self._build_query(
            subject, after, before, has_attachment, is_unread, keywords
        )

        params = {"userId": self.user_id, "maxResults": max_results, "q": query}
        if labels:
            params["labelIds"] = labels
        if page_token:
            params["pageToken"] = page_token

        response = self.service.users().messages().list(**params).execute()
        self.next_page_token = response.get("nextPageToken")
        if response.get("messages") is None:
            raise ValueError("Gmail account does not have any emails")
        full_msg_list: List[FullMessage] = [
            {msg["id"]: self.fetch_full_message(msg["id"])}
            for msg in response.get("messages")
        ]
        email: str = get_user_email(self.cred_details)
        user_token: int = AuthManager().get_token(email)
        with get_db_session() as session:
            EmailStorageService(session, user_token).store_emails_from_fetcher(
                full_msg_list
            )
        return response

    def fetch_full_message(self, message_id: str) -> Dict:
        return (
            self.service.users()
            .messages()
            .get(userId=self.user_id, id=message_id, format="full")
            .execute()
        )

    def get_next_page_token(self) -> Optional[str]:
        return self.next_page_token
