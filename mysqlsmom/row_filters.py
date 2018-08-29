# coding=utf-8


def changed_fields(event, fields):
    before_values = event.get("before_values", {})
    values = event["values"]
    for k in fields:
        if before_values.get(k) != values.get(k):
            return True
    return False
