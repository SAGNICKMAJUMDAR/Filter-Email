from celery import Celery, shared_task, Task
from celery.schedules import crontab
from setup import CELERY_BACKEND_URL, BROKER

from typing import List, Dict, Any, Optional
from uuid import UUID
import json

from models import EmailStatus, UserToken, Email, EmailAddress, EmailParticipant
from sqlalchemy import func, delete, exists

from google_auth_Manager import AuthManager
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email_fetcher_service import EmailFetcherService, get_db_session


app = Celery("gmail_application", broker=BROKER, backend=CELERY_BACKEND_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_scheduler="celery.beat:PersistentScheduler",
)

app.conf.beat_schedule = {
    "sync-all-emails-every-15-minutes": {
        "task": "sync_all_user_emails",
        "schedule": crontab(minute="*/15"),
    },
    "mark-deleted-every-every-day": {
        "task": "fetch_deleted_emails_for_all_users",
        "schedule": crontab(hour=0, minute=0),
    },
    "remove-deleted-emails-every-day": {
        "task": "remove_deleted_emails",
        "schedule": crontab(hour=0, minute=0),
    },
    "remove-unused-email-address-every-day": {
        "task": "remove_email_address",
        "schedule": crontab(hour=0, minute=0),
    },
}


class RetryTask(Task):
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 6}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


def get_credentials(user_token_id: UUID, scope: List[str]) -> Credentials:
    token_details: UserToken = AuthManager().get_token_by_id(user_token_id)
    return Credentials.from_authorized_user_info(
        json.loads(token_details["token_data"]), scope
    )


@app.task(name="sync_all_user_emails")
def sync_all_user_emails():
    "Sync all gmail accounts"
    with get_db_session() as session:
        user_token_ids = session.query(UserToken.id).all()
    for (user_token_id,) in user_token_ids:
        sync_user_emails.apply_async(args=[str(user_token_id)])


@app.task(name="sync_user_emails")
def sync_user_emails(user_token_id):
    "Sync individual gmail account"
    try:
        cred_details: Credentials = get_credentials(
            user_token_id, ["https://www.googleapis.com/auth/gmail.readonly"]
        )
        email_fetcher_service = EmailFetcherService(cred_details=cred_details)
        latest_date = email_fetcher_service.get_latest_internal_date(user_token_id)
        if latest_date is not None:
            email_fetcher_service.fetch_emails(after=latest_date)
    except Exception as e:
        raise (f"[sync_user_emails ERROR] {e}")


@app.task
@shared_task(bind=True, base=RetryTask)
def mark_email_status(self, message_ids: List[str], gmail_account_id: UUID):
    "Mark Email status as deleted"
    try:
        EmailFetcherService().update_email_status(
            message_ids, EmailStatus.DELETED, gmail_account_id
        )
    except Exception as e:
        raise (f"[ERROR] Failed mark email as deleted: {e}")


@app.task(name="fetch_deleted_emails_for_all_users")
def fetch_deleted_emails_for_all_users():
    "Fetch deleted emails for all gmail accounts"
    with get_db_session() as session:
        user_token_ids = session.query(UserToken.id).all()
    for (user_token_id,) in user_token_ids:
        check_deleted_emails.apply_async(args=[str(user_token_id)])


@app.task(name="check_deleted_emails")
def check_deleted_emails(user_token_id: str):
    "Fetch deleted gmail for a single account"
    cred_details: Credentials = get_credentials(
        user_token_id, ["https://www.googleapis.com/auth/gmail.readonly"]
    )
    service = build("gmail", "v1", credentials=cred_details)

    result = service.users().messages().list(userId="me").execute()
    gmail_ids = {msg["id"] for msg in result.get("messages", [])}

    gmail_ids = set()
    page_token = None

    try:
        while True:
            result = (
                service.users()
                .messages()
                .list(userId="me", maxResults=500, pageToken=page_token)
                .execute()
            )

            gmail_ids.update(msg["id"] for msg in result.get("messages", []))

            page_token = result.get("nextPageToken")
            if page_token is None:
                break

        local_emails: List[Dict[str, Any]] = EmailFetcherService(
            cred_details=cred_details
        ).fetched_stored_email(user_token_id)
        delete_message_ids = [
            email["message_id"]
            for email in local_emails
            if email["message_id"] not in gmail_ids
            and email["status"] != EmailStatus.DELETED.value
        ]
        mark_email_status.apply_async(args=[delete_message_ids, user_token_id])
    except Exception as e:
        raise (f"[ERROR] Failed detecting deleted emails: {e}")


@app.task(name="remove_deleted_emails")
def remove_deleted_emails():
    "Delete emails permanently"
    with get_db_session() as session:
        session.execute(delete(Email).where(Email.status == EmailStatus.DELETED))


@app.task(name="remove_email_address")
def remove_email_address():
    "Remove email addresses that are not referred in EmailParticipants"
    with get_db_session() as session:
        session.query(EmailAddress).filter(
            ~exists().where(EmailParticipant.email_address_id == EmailAddress.id)
        ).delete(synchronize_session=False)
