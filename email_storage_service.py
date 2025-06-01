from httplib2 import Credentials
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from typing import TypedDict, List, Tuple, Dict
from models import Email, EmailAddress, EmailParticipant, RoleEnum, UserToken
from email.utils import parsedate_to_datetime


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

    def extract_email_info(self, raw: str) -> List[str]:
        "Extract Recepient Email Addresses"
        if not raw:
            return []
        return [self.extract_email(addr) for addr in raw.split(",")]
    
    @staticmethod
    def form_db_data(
        address_list:List,
        email_id: uuid.UUID,
        participants_to_add: List[str], 
        addresses_to_add: List[str], 
        email_address_id_map:Dict[str, uuid.UUID],
        role: RoleEnum
    ) -> None:
        "Form Db data"

        for addr in address_list:
            address = addr.lower().strip()
            if email_address_id_map.get(address) is None:
                email_address_id_map[address] = uuid.uuid4()

            addresses_to_add.append(
                {
                    "id": email_address_id_map[address],
                    "address": address,
                }
            )
            participants_to_add.append(
                {
                    "email_id": email_id,
                    "email_address_id": email_address_id_map[address],
                    "role": role,
                }
            )

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
            subject:str = headers.get("Subject")
            sender_address:str = self.extract_email(headers.get("From", "")).lower().strip()
            recipient_addresses:List[str] = self.extract_email_info(headers.get("To", ""))
            cced_addresses:List[str] = self.extract_email_info(headers.get("Cc", ""))
            bcced_addresses:List[str] = self.extract_email_info(headers.get("Bcc", ""))
            internal_date:datetime = datetime.fromtimestamp(int(full_msg["internalDate"]) / 1000)
            received_date = parsedate_to_datetime(headers.get("Date"))

            email_id: uuid = uuid.uuid4()
            email = {
                "id": email_id,
                "message_id": msg_id,
                "gmail_account_id": self.user_token["id"],
                "subject": subject,
                "received_date": received_date,
                "internal_date": internal_date,
            }
            emails_to_add.append(email)

            self.form_db_data([sender_address], email_id, participants_to_add,  addresses_to_add, email_address_id_map, RoleEnum.SENDER)
            self.form_db_data(recipient_addresses, email_id, participants_to_add,  addresses_to_add, email_address_id_map, RoleEnum.RECIPIENT)
            self.form_db_data(cced_addresses, email_id, participants_to_add,  addresses_to_add, email_address_id_map, RoleEnum.CC)
            self.form_db_data(bcced_addresses, email_id, participants_to_add,  addresses_to_add, email_address_id_map, RoleEnum.BCC)
            
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
        
