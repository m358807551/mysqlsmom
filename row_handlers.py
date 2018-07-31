# coding=utf-8
import copy


def ignored_fields(row, fields):
    row = copy.deepcopy(row)
    for field in fields:
        if field in row:
            del row[field]
    return row


def split(row, field, flag):
    row = copy.deepcopy(row)
    if row[field]:
        row[field] = row[field].split(flag)
    else:
        row[field] = []
    return row


def set_field(row, field, value):
    row = copy.deepcopy(row)
    row[field] = value
    return row


def comma_split(row, field):
    row = copy.deepcopy(row)
    if row[field]:
        row[field] = row[field].split(",")
    else:
        row[field] = []
    return row


def replace_fields(row, **name2new_names):
    row = copy.deepcopy(row)
    for name, new_names in name2new_names.items():
        value = row[name]
        del row[name]
        for new_name in new_names:
            row[new_name] = value
    return row


def set_id(row, field):
    row = copy.deepcopy(row)
    row["_id"] = row[field]
    return row


def only_fields(row, fields):
    new_row = dict()
    for field in fields:
        new_row[field] = row[field]
    return new_row


def script(row, inline):
    doc = copy.deepcopy(row)
    exec inline
    return doc


def classify_zh_en(row, field):
    row = copy.deepcopy(row)

    def has_chinese(string):
        for char in string:
            if u'\u4e00' <= char <= u'\u9fff':
                return True
        return False

    value = row[field]
    if not value:
        row[field + "_zh"] = ""
        row[field + "_en"] = ""
        return row
    if isinstance(value, list):
        zh, en = [], []
        for v in value:
            if has_chinese(v):
                zh.append(v)
            else:
                en.append(v)
        row[field + "_zh"] = zh
        row[field + "_en"] = en
    else:
        if has_chinese(value):
            row[field+"_zh"] = value
            row[field+"_en"] = ""
        else:
            row[field + "_zh"] = ""
            row[field + "_en"] = value
    return row


def do_sql(row, sql, connection, database):
    from peewee import MySQLDatabase, Model

    db = MySQLDatabase(database,
                       **{'host': connection["host"], 'password': connection["passwd"], 'port': connection["port"],
                          'user': connection["user"]})

    class MyModel(Model):
        class Meta:
            database = db

    import re
    keys = re.findall("\{(\w+)\}", sql)
    params = [row[key] for key in keys]

    sql = re.sub("\{\w+\}", "%s", sql)
    result = list(MyModel.raw(sql, *params).dicts())
    db.close()
    return result
