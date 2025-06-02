from re import split
from auth_utility import VALID_FIELDS_PREDICATE_MAP, VALID_ACTIONS, CONFLICTING_ACTIONS


class FileValidator:

    def validate_rules(self, data):
        "Validate rules in json file provided by the  user"
        predicate = data.get("predicate", "").lower()
        if predicate not in ["all", "any"]:
            raise ValueError(f"Invalid rule predicate at top-level: {predicate}")
        rules = data.get("rules", [])
        if not rules:
            raise ValueError("No rules defined")
        for rule in rules:
            if rule.get("field") is None:
                raise ValueError("'field' is missing for one of the rules")
            if rule.get("predicate") is None:
                raise ValueError("'predicate' is missing for one of the rules")
            if rule.get("value") is None or str(rule["value"]).strip() == "":
                raise ValueError("'value' is missing for one of the rules")

            field = rule["field"].lower()
            predicate = rule["predicate"].lower()
            value = rule["value"].lower()

            if field == "received date/time" and value.split()[1] not in (
                "day",
                "days",
                "month",
                "months",
                "year",
                "years",
            ):
                raise ValueError(f"{field} value is incorrect  -  {value}")

            if field not in VALID_FIELDS_PREDICATE_MAP:
                raise ValueError(
                    f"field {field} is incorrect, please check the corresponding json file"
                )
            if predicate not in VALID_FIELDS_PREDICATE_MAP[field]:
                raise ValueError(
                    f"predicate {predicate} is incorrect for the corresponding {field}"
                )

    def validate_actions(self, data):
        "Validate the actions provided in the json file"
        actions = data.get("actions", [])
        if not actions:
            raise ValueError("Actions rules defined")
        seen = set()
        move_actions = []
        for action in actions:
            if action not in VALID_ACTIONS:
                raise ValueError(f"Invalid action: {action}")
            if action.startswith("move:"):
                move_actions.append(action)
            seen.add(action)
        for action1, action2 in CONFLICTING_ACTIONS:
            if action1 in seen and action2 in seen:
                raise ValueError(f"Conflicting actions: {action1} and {action2}")
        if len(move_actions) > 1:
            raise ValueError(f"Multiple move actions are not allowed: {move_actions}")
        if "delete_permanent" in seen and len(seen) > 1:
            raise ValueError("delete_permanent cannot be combined with other actions")
