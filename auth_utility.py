from googleapiclient.discovery import build
from models import RoleEnum


VALID_FIELDS_PREDICATE_MAP = {
    "sender": ["contains", "does not contain", "equals", "does not equal"],
    "recipient": ["contains", "does not contain", "equals", "does not equal"],
    "subject": ["contains", "does not contain", "equals", "does not equal"],
    "received date/time":  ["less than", "greater than", "equals"]
}


VALID_ACTIONS = {
    "mark_as_read",
    "mark_as_unread",
    "mark_important",
    "mark_unimportant",
    "star",
    "unstar",
    "delete_permanent",
    "move:inbox",
    "move:spam",
    "move:archive",
    "move:trash"
}

CONFLICTING_ACTIONS = (
    ("mark_as_read", "mark_as_unread"),
    ("mark_important", "mark_unimportant"),
    ("star", "unstar")
)


role_map = {
    "sender": RoleEnum.SENDER, 
    "recipient": RoleEnum.RECIPIENT, 
    "cc": RoleEnum.CC, 
    "bcc": RoleEnum.BCC
}

def get_user_email(credential_detail):
    service = build("gmail", "v1", credentials=credential_detail)
    profile = service.users().getProfile(userId="me").execute()
    return profile["emailAddress"]
