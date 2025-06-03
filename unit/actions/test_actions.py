import pytest
from actions import Actions

from conftest import DummyGmailService


def test_mark_as_read_action(dummy_service, monkeypatch):
    actions = Actions(dummy_service)
    actions.perform_batch(["msg1", "msg2"], ["mark_as_read"], gmail_account_id="acc123")

    assert dummy_service.modified is True
    assert "UNREAD" in dummy_service.batch_modify_body["removeLabelIds"]


def test_mark_as_unread_action(dummy_service, monkeypatch):
    actions = Actions(dummy_service)
    actions.perform_batch(["msg3"], ["mark_as_unread"], gmail_account_id="acc123")

    assert dummy_service.modified is True
    assert "UNREAD" in dummy_service.batch_modify_body["addLabelIds"]


def test_delete_permanent(dummy_service, monkeypatch):
    monkeypatch.setattr("actions.mark_email_status.apply_async", lambda args: None)

    actions = Actions(dummy_service)
    actions.perform_batch(
        ["msg4", "msg5"], ["delete_permanent"], gmail_account_id="acc123"
    )
    assert dummy_service.deleted is True
    assert dummy_service.batch_delete_ids == ["msg4", "msg5"]


def test_move_to_spam(dummy_service):
    actions = Actions(dummy_service)
    actions.perform_batch(["msg6"], ["move:spam"], gmail_account_id="acc123")
    assert "SPAM" in dummy_service.batch_modify_body["addLabelIds"]
    assert "INBOX" in dummy_service.batch_modify_body["removeLabelIds"]


def test_star_and_unstar(dummy_service):
    actions = Actions(dummy_service)
    actions.perform_batch(["msg7"], ["star"], gmail_account_id="acc123")
    assert "STARRED" in dummy_service.batch_modify_body["addLabelIds"]

    actions.perform_batch(["msg7"], ["unstar"], gmail_account_id="acc123")
    assert "STARRED" in dummy_service.batch_modify_body["removeLabelIds"]
