import datetime
from typing import List, Dict, Union
from query_builder import QueryBuilder

class EmailRuleProcessor:
    def __init__(self, db_session):
        self.db = db_session
        self.sql_converter = QueryBuilder()

    def process_rules(self, rules)->List[Dict[str, Union[str, int, datetime.datetime]]]:
            "Fetch Emails from db based on the rules"
            query = self.sql_converter.build_combined_query(self.db, rules)
            emails = query.all()
            result=[email.to_dict() for email in emails]
            return result