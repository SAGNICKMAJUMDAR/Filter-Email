import pytest


class DummyGmailService:
    def __init__(self):
        self.deleted = False
        self.modified = False
        self.batch_delete_ids = []
        self.batch_modify_body = {}
        self.batch_modified_ids = []

    class Users:
        class Messages:
            def __init__(self, outer):
                self.outer = outer

            def batchDelete(self, userId, body):
                self.outer.deleted = True
                self.outer.batch_delete_ids = body["ids"]
                return self

            def batchModify(self, userId, body):
                self.outer.modified = True
                self.outer.batch_modify_body = body
                self.outer.batch_modified_ids = body["ids"]
                return self

            def execute(self):
                return {"status": "success"}

        def __init__(self, outer):
            self.messages_obj = self.Messages(outer)

        def messages(self):
            return self.messages_obj

    def users(self):
        return self.Users(self)


@pytest.fixture()
def dummy_service():
    return DummyGmailService()
