from models import RoleEnum, EmailStatus, Email, EmailAddress, EmailParticipant

from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from auth_utility import role_map


class QueryBuilder:

    @staticmethod
    def get_date_threshold(unit: str, number: int):
        "Get threshold date in month and years"

        if unit in ("day", "days"):
            return func.current_date() - timedelta(days=number)
        if unit in ("month", "months"):
            return datetime.now() - relativedelta(months=2)
        return datetime.now() - relativedelta(years=2)

    def build_combined_query(self, session, rules):
        "Build query to fetch emails from db based on the rules"

        conditions = []
        for rule in rules["rules"]:
            field = rule["field"].lower()
            predicate = rule["predicate"].lower()
            value = rule["value"]

            if field in ("sender", "recipient", "cc", "bcc"):
                role_enum = role_map[field]
                subquery = (
                    session.query(Email.id)
                    .join(EmailParticipant)
                    .join(EmailAddress)
                    .filter(
                        EmailParticipant.role == role_enum,
                        Email.status != EmailStatus.DELETED,
                    )
                )
                if predicate == "contains":
                    subquery = subquery.filter(EmailAddress.address.ilike(f"%{value}%"))
                elif predicate == "equals":
                    subquery = subquery.filter(EmailAddress.address == value)
                elif predicate == "does not contain":
                    subquery = subquery.filter(
                        ~EmailAddress.address.ilike(f"%{value}%")
                    )
                elif predicate == "does not equal":
                    subquery = subquery.filter(EmailAddress.address != value)
                conditions.append(Email.id.in_(subquery))

            elif field == "subject":
                column = Email.subject
                if predicate == "contains":
                    conditions.append(column.ilike(f"%{value}%"))
                elif predicate == "equals":
                    conditions.append(column == value)
                elif predicate == "does not contain":
                    conditions.append(~column.ilike(f"%{value}%"))
                elif predicate == "does not equal":
                    conditions.append(column != value)

            elif field == "received date/time":
                duration_value: int
                duration_unit: str
                column = Email.received_date
                duration_value, duration_unit = value.split()
                if "less than" in predicate:
                    conditions.append(
                        column
                        >= self.get_date_threshold(duration_unit, int(duration_value))
                    )
                elif "greater than" in predicate:
                    conditions.append(
                        column
                        < self.get_date_threshold(duration_unit, int(duration_value))
                    )
                elif "equals" in predicate:
                    conditions.append(func.date(column) == func.current_date())
        combiner = and_ if rules["predicate"].lower() == "all" else or_
        filter_conditions = combiner(*conditions)

        combined_query = session.query(Email).filter(filter_conditions).limit(1000)
        return combined_query
