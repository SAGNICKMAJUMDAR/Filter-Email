import datetime
import email
from uuid import UUID
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
from sqlalchemy.exc import SQLAlchemyError

from session_manager import get_db_session
from models import EmailStatus, UserToken, Email

from email_storage_service import EmailStorageService, FullMessage
from auth_utility import get_user_email
from resolver import ServiceManager
from typing import Optional


@ServiceManager.register("email_fetcher")
class EmailFetcherService:
    def __init__(self, cred_details: Optional[Credentials] = None):
        self.cred_details = cred_details
        self.service = (
            build("gmail", "v1", credentials=cred_details)
            if cred_details is not None
            else None
        )
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
            "after": int(after) if after is not None else None,
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
        user_token: int = ServiceManager.get("auth")().get_token(email)
        with get_db_session() as session:
            EmailStorageService(session).store_emails_from_fetcher(
                full_msg_list, user_token
            )
        return response

    def fetch_full_message(self, message_id: str) -> Dict:
        "Fetch details of each email from gmail account"
        return (
            self.service.users()
            .messages()
            .get(userId=self.user_id, id=message_id, format="full")
            .execute()
        )

    def get_next_page_token(self) -> Optional[str]:
        "Return next page token"
        return self.next_page_token

    def get_latest_internal_date(self, gmail_account_id) -> Optional[int]:
        "Fetch internal date of the latest stored email"
        with get_db_session() as session:
            latest: Optional[datetime] = EmailStorageService(
                session
            ).get_latest_internal_date(gmail_account_id)
        return int(latest.timestamp()) if latest else None

    def update_email_status(
        self, message_ids: List[str], status: EmailStatus, gmail_account_id: UUID
    ) -> None:
        "update email status"
        with get_db_session() as session:
            EmailStorageService(session).update_email_status(
                message_ids, status, gmail_account_id
            )

    def fetched_stored_email(self, gmail_account_id) -> List[Dict[str, Any]]:
        "Fetch stored emails from db for a gmail account"
        with get_db_session() as session:
            email_objs: List[Email] = EmailStorageService(session).fetched_stored_email(
                gmail_account_id
            )
            email_details: List[Dict[str, Any]] = [
                email.to_dict() for email in email_objs
            ]
        return email_details
