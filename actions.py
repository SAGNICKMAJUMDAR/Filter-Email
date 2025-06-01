from sqlalchemy import delete
from email_fetcher_service import get_db_session
from models import Email

class Actions:

    class ActionMapper:
          
        _action_mapper = {}
           
        @classmethod
        def action_mapper(cls, action_name):
            def wrapper(fn):
                cls._action_mapper[action_name] = fn
                return fn
            return wrapper
    
    action_mapper_obj =  ActionMapper()
    
    def __init__(self, gmail_service):
        self.service = gmail_service
    
    def perform_batch(self, message_ids, actions) -> None:

        "Perform batch actions on fetched emails"
    
        add_labels = []
        remove_labels = []
        delete_ids = []

        for action in actions:
            if action == "delete_permanent":
                delete_ids.extend(message_ids)
            else:
                self.action_mapper_obj._action_mapper[action](self, add_labels, remove_labels)
        if delete_ids:
            self.service.users().messages().batchDelete(
                userId='me',
                body={"ids": message_ids}
            ).execute()
            # NOTE: a task should be triggered to remove the emails in db
            with get_db_session() as db_session:
                db_session.execute(
                    delete(Email).where(Email.message_id.in_(message_ids))
                )
        
        if message_ids and add_labels or remove_labels:
            a=self.service.users().messages().batchModify(
                userId='me',
                body={  
                    'ids': message_ids,
                    'addLabelIds': add_labels,
                    'removeLabelIds': remove_labels
                }
            ).execute()
    
    @action_mapper_obj.action_mapper("mark_as_read")
    def mark_as_read(self, _add_labels, remove_labels):
        remove_labels.append("UNREAD")

    @action_mapper_obj.action_mapper("mark_as_unread")
    def mark_as_unread(self, add_labels, _remove_labels):
        add_labels.append("UNREAD")

    @action_mapper_obj.action_mapper("mark_important")
    def mark_important(self, add_labels, _remove_labels):
        add_labels.append("IMPORTANT")

    @action_mapper_obj.action_mapper("mark_unimportant")
    def mark_unimportant(self, _add_labels, remove_labels):
        remove_labels.append("IMPORTANT")

    @action_mapper_obj.action_mapper("star")
    def star(self, add_labels, _remove_labels):
        add_labels.append("STARRED")

    @action_mapper_obj.action_mapper("unstar")
    def unstar(self, _add_labels, remove_labels):
        remove_labels.append("STARRED")

    @action_mapper_obj.action_mapper("move:spam")
    def move_to_spam(self, add_labels, remove_labels):
        add_labels.append("SPAM")
        remove_labels.append("INBOX")

    @action_mapper_obj.action_mapper("move:inbox")
    def move_to_inbox(self, add_labels, _remove_labels):
        add_labels.append("INBOX")

    @action_mapper_obj.action_mapper("move:archive")
    def move_to_archive(self, _add_labels, remove_labels):
        remove_labels.append("INBOX")

    @action_mapper_obj.action_mapper("move:trash")
    def move_to_trash(self, add_labels, _remove_labels):
        add_labels.append("TRASH")