from httplib2 import Credentials
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from typing import TypedDict, List, Tuple
from models import Email, EmailAddress, EmailParticipant, RoleEnum, UserToken


class Header(TypedDict):
    name: str
    value: str


class Payload(TypedDict, total=False):
    mimeType: str
    headers: List[Header]


class FullMessage(TypedDict, total=False):
    id: str
    threadId: str
    labelIds: List[str]
    snippet: str
    internalDate: str
    payload: Payload


class EmailStorageService:
    def __init__(self, db_session: Session, user_token: UserToken):
        self.db_session = db_session
        self.user_token = user_token
        self._email_cache = {}
        self._address_cache = {}

    def extract_email(self, raw: str) -> str:
        "Extract Sender Email Address"
        if "<" in raw:
            return raw.split("<")[1].split(">")[0].strip()
        return raw.strip()

    def extract_recipients(self, raw: str) -> List[str]:
        "Extract Recepient Email Addresses"
        if not raw:
            return []
        return [self.extract_email(addr) for addr in raw.split(",")]

    def store_emails_from_fetcher(self, msg_list: List[FullMessage]) -> None:
        """
        Store emails fetched from gmail account
        1. Extract email address of sender.
        2. Extract email address of recepients.
        3. Store email details in Email table.
        4. Store Individual email address in EmailAddress table.
        5. Map the Email and it sender and recepients in Email Participant table
        """
        emails_to_add: List[str] = []
        participants_to_add: List[int] = []
        addresses_to_add: List[str] = []
        result: List[Tuple[str, uuid.UUID]] = self.db_session.query(
            EmailAddress.address, EmailAddress.id
        ).all()
        email_address_id_map = {address: id_ for address, id_ in result}

        for msg_obj in msg_list:
            msg_id, full_msg = next(iter(msg_obj.items()))
            headers = {
                header["name"]: header["value"]
                for header in full_msg["payload"]["headers"]
            }
            subject = headers.get("Subject")
            sender_address = self.extract_email(headers.get("From", "")).lower().strip()
            recipient_addresses = self.extract_recipients(headers.get("To", ""))
            internal_date = datetime.fromtimestamp(int(full_msg["internalDate"]) / 1000)

            email_id: uuid = uuid.uuid4()
            email = {
                "id": email_id,
                "message_id": msg_id,
                "gmail_account_id": self.user_token["id"],
                "subject": subject,
                "internal_date": internal_date,
            }
            emails_to_add.append(email)

            if email_address_id_map.get(sender_address) is None:
                email_address_id_map[sender_address] = uuid.uuid4()

            addresses_to_add.append(
                {"id": email_address_id_map[sender_address], "address": sender_address}
            )

            participants_to_add.append(
                {
                    "email_id": email_id,
                    "email_address_id": email_address_id_map[sender_address],
                    "role": RoleEnum.sender,
                }
            )

            for recipient_addr in recipient_addresses:
                recipient_address = recipient_addr.lower().strip()
                if email_address_id_map.get(recipient_address) is None:
                    email_address_id_map[recipient_address] = uuid.uuid4()

                addresses_to_add.append(
                    {
                        "id": email_address_id_map[recipient_address],
                        "address": recipient_address,
                    }
                )
                participants_to_add.append(
                    {
                        "email_id": email_id,
                        "email_address_id": email_address_id_map[recipient_address],
                        "role": RoleEnum.recipient,
                    }
                )
        self.db_session.execute(
            insert(Email)
            .values(emails_to_add)
            .on_conflict_do_nothing(index_elements=["message_id", "gmail_account_id"])
        )
        self.db_session.flush()
        self.db_session.execute(
            insert(EmailAddress)
            .values(addresses_to_add)
            .on_conflict_do_nothing(index_elements=["address"])
        )
        self.db_session.flush()
        self.db_session.execute(
            insert(EmailParticipant)
            .values(participants_to_add)
            .on_conflict_do_nothing(
                index_elements=["email_id", "email_address_id", "role"]
            )
        )
