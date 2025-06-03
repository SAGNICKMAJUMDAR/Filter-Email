import argparse
import os

from google_auth_Manager import AuthManager
from email_fetcher_service import EmailFetcherService, get_db_session
from models import UserToken


def parse_args():
    parser = argparse.ArgumentParser(description="Process Gmail fetch parameters.")

    parser.add_argument(
        "--credentials", type=str, help="Path to the credentials.json file"
    )
    parser.add_argument(
        "--email", type=str, help="Email address for which to fetch messages"
    )
    parser.add_argument("--reauth", action="store_true", help="Force reauthentication")
    parser.add_argument(
        "--limit", type=int, default=10, help="Number of emails to fetch (default: 10)"
    )
    parser.add_argument("--labels", type=str, help="List of Gmail labels to filter")
    parser.add_argument("--subject", type=str, help="Subject to filter by")
    parser.add_argument(
        "--after",
        type=str,
        help="Only fetch emails after this date (format: YYYY/MM/DD or timestamp)",
    )
    parser.add_argument(
        "--before",
        type=str,
        help="Only fetch emails before this date (format: YYYY/MM/DD or timestamp)",
    )
    parser.add_argument(
        "--has_attachment",
        action="store_true",
        help="Only include emails with attachments",
    )
    parser.add_argument(
        "--is_unread", action="store_true", help="Only include unread emails"
    )
    parser.add_argument(
        "--keywords", type=str, nargs="*", help="List of keywords to search for"
    )
    parser.add_argument(
        "--page_token", type=str, help="Gmail API page token for pagination"
    )

    return parser.parse_args()


def main():
    args = parse_args()
    arg_value_map = {key: value for key, value in vars(args).items()}
    if arg_value_map["email"] is None and arg_value_map["credentials"] is None:
        args.error("You must provide either --email or --credential_path")
    if arg_value_map["email"] is not None and arg_value_map["credentials"] is None and arg_value_map["reauth"]:
        args.error("You must provide both --credential_path when --reauth is True")
    
    auth = AuthManager(
        email=arg_value_map["email"],
        credential_path=arg_value_map["credentials"],
        scope=[
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://mail.google.com/",
        ],
        re_auth=arg_value_map["reauth"],
    )
    cred_details, email = auth.authenticate()
    with get_db_session() as db_session:
        id = db_session.query(UserToken.id).filter(UserToken.email == email).scalar()
    response = EmailFetcherService(cred_details=cred_details).fetch_emails(
        max_results=arg_value_map["limit"],
        labels=arg_value_map["labels"],
        subject=arg_value_map["subject"],
        after=arg_value_map["after"],
        before=arg_value_map["before"],
        has_attachment=arg_value_map["has_attachment"],
        is_unread=arg_value_map["is_unread"],
        keywords=arg_value_map["keywords"],
        page_token=arg_value_map["page_token"],
    )
    print(f"page_token {response.get('nextPageToken')}")


if __name__ == "__main__":
    main()
