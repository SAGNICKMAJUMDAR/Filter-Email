import argparse
import os
import json
from typing import Dict, Any

from models import UserToken
from rules_file_validator import FileValidator
from rule_processor import EmailRuleProcessor
from email_fetcher_service import EmailFetcherService, get_db_session
from actions import Actions
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


def main():

    parser = argparse.ArgumentParser(description="Perform actions on fetched emails.")
    parser.add_argument(
        "--rules", type=str, required=True, help="Path to the rules.json file"
    )
    parser.add_argument(
        "--email", type=str, required=True, help="Email address to be provided"
    )
    args = parser.parse_args()
    arg_value_map = {key: value for key, value in vars(args).items()}
    with open(arg_value_map["rules"], "r") as f:
        data = json.load(f)

    validator_obj = FileValidator()
    validator_obj.validate_rules(data)
    validator_obj.validate_actions(data)

    with get_db_session() as db_session:
        emails = EmailRuleProcessor(db_session).process_rules(data)
    with get_db_session() as db_session:
        user_token: UserToken = (
            db_session.query(UserToken)
            .filter(UserToken.email == arg_value_map["email"])
            .first()
        )
        user_token_details: Dict[str, Any] = user_token.to_dict()

    cred_details: Credentials = Credentials.from_authorized_user_info(
        json.loads(user_token_details["token_data"]),
        [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.modify",
            "https://mail.google.com/",
        ],
    )
    message_ids = [email["message_id"] for email in emails]
    service = build("gmail", "v1", credentials=cred_details)
    Actions(service).perform_batch(
        message_ids, data["actions"], user_token_details["id"]
    )


if __name__ == "__main__":
    main()
