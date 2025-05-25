from googleapiclient.discovery import build


def get_user_email(credential_detail):
    service = build("gmail", "v1", credentials=credential_detail)
    profile = service.users().getProfile(userId="me").execute()
    return profile["emailAddress"]
