# coding=utf-8
import sys
import importlib
import logging
import json
import datetime
import copy
from collections import defaultdict

import redis
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import DeleteRowsEvent, WriteRowsEvent, UpdateRowsEvent
from pymysqlreplication.event import RotateEvent
from elasticsearch import Elasticsearch
from elasticsearch import helpers

import row_handlers
import row_filters


logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s")


class Cache(object):
    def __init__(self, config_name):
        self.r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        self.log_file = "%s_%s" % (config_name, "log_file")
        self.log_pos = "%s_%s" % (config_name, "log_pos")

    def get_log_file(self):
        return self.r.get(self.log_file)

    def get_log_pos(self):
        log_pos = self.r.get(self.log_pos)
        if log_pos:
            return int(log_pos)
        else:
            return None

    def set_log_file(self, log_file):
        self.r.set(self.log_file, log_file)

    def set_log_pos(self, log_pos):
        self.r.set(self.log_pos, log_pos)


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return '{0.year:4d}-{0.month:02d}-{0.day:02d} {0.hour:02d}:{0.minute:02d}:{0.second:02d}'.format(obj)
        elif isinstance(obj, datetime.date):
            return '{0.year:4d}-{0.month:02d}-{0.day:02d}'.format(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def do_pipeline(pipeline, row):
    if isinstance(row, dict):
        row = [row]

    # row 可能是个列表或迭代器
    for line in pipeline:
        row_ = []
        for r in row:
            func_name, kwargs = line.items()[0]
            func = getattr(row_handlers, func_name)
            r_new = func(r, **kwargs)
            if isinstance(r_new, dict):
                row_.append(r_new)
            else:
                row_.extend(list(r_new))
        row = row_
    rows = row
    return rows


def to_dest(dest, rows):
    if isinstance(rows, dict):
        rows = [rows]
    for row in rows:
        if dest.keys()[0] == "es":
            row = copy.deepcopy(row)
            _id = row["_id"]
            del row["_id"]

            es_config = dest["es"]

            es = Elasticsearch(es_config["nodes"])
            # 有则更新，无则插入
            # try:
            logging.info(json.dumps(row, cls=DateEncoder))
            docs = [{"_id": _id, "_type": es_config["type"], "_index": es_config["index"],
                     "_source": {'doc': row, 'doc_as_upsert': True}, '_op_type': 'update'}]
            helpers.bulk(es, docs)
            # except Exception, e:
            #     logging.warn(traceback.format_exc())


def handle_init_stream(config):
    connection = config.CONNECTION
    for task in config.TASKS:
        import peewee
        from peewee import MySQLDatabase

        db = MySQLDatabase(task["stream"]["database"],
                           **{'host': connection["host"], 'password': connection["passwd"], 'port': connection["port"],
                              'user': connection["user"]})

        pk = task["stream"].get("pk")
        if not pk:
            pk = {"field": "id", "type": "int"}

        class MyModel(peewee.Model):
            _pk = {
                "char": peewee.CharField(primary_key=True),
                "int": peewee.IntegerField(primary_key=True)
            }[pk["type"]]

            class Meta:
                database = db
        setattr(MyModel, pk["field"], MyModel._pk)

        query = MyModel.raw(task["stream"]["sql"]).dicts().iterator()
        for row in query:
            for job in task["jobs"]:
                event = {
                    "action": "insert",
                    "values": row
                }
                if event["action"] in job["actions"]:
                    rows = do_pipeline(job["pipeline"], event["values"])
                    to_dest(job["dest"], rows)
        db.close()


def handle_binlog_stream(config):
    cache = Cache(config.SLAVE_UUID)

    # 该操作可以关闭旧有binlog连接
    stream_binlog = BinLogStreamReader(
        connection_settings=config.BINLOG_CONNECTION,
        server_id=config.SERVER_ID,
        blocking=False,
        resume_stream=True,
        slave_uuid=config.SLAVE_UUID
    )
    stream_binlog.fetchone()

    only_schemas = set()
    only_tables = set()
    event2jobs = defaultdict(list)
    for task in config.TASKS:
        only_schemas.add(task["stream"]["database"])
        only_tables.add(task["stream"]["table"])

        for job in task["jobs"]:
            for action in job["actions"]:
                event = "{host}_{schema}_{table}_{action}".format(host=config.BINLOG_CONNECTION["host"],
                                                                  schema=task["stream"]["database"], table=task["stream"]["table"], action=action)
                event2jobs[event].append(job)

    stream_binlog = BinLogStreamReader(
        connection_settings=config.BINLOG_CONNECTION,
        server_id=config.SERVER_ID,
        blocking=True,
        only_events=[WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent, RotateEvent], only_schemas=only_schemas,
        only_tables=only_tables,
        freeze_schema=True,
        log_file=cache.get_log_file(),
        log_pos=cache.get_log_pos(),
        resume_stream=True,
        slave_uuid=config.SLAVE_UUID
    )

    for binlogevent in stream_binlog:
        if isinstance(binlogevent, RotateEvent):
            cache.set_log_file(binlogevent.next_binlog)
            cache.set_log_pos(binlogevent.position)
        else:
            print binlogevent.packet.log_pos
            for row in binlogevent.rows:
                event = {"host": binlogevent._ctl_connection.host, "schema": binlogevent.schema,
                         "table": binlogevent.table,
                         "timestamp": datetime.datetime.fromtimestamp(binlogevent.timestamp).strftime('%Y-%m-%d %H:%M:%S')}
                # 组装event
                if isinstance(binlogevent, DeleteRowsEvent):
                    event["action"] = "delete"
                    event["values"] = dict(row["values"].items())
                elif isinstance(binlogevent, UpdateRowsEvent):
                    event["action"] = "update"
                    event["before_values"] = dict(row["before_values"].items())
                    event["values"] = dict(row["after_values"].items())
                elif isinstance(binlogevent, WriteRowsEvent):
                    event["action"] = "insert"
                    event["values"] = dict(row["values"].items())

                event_type = "{host}_{schema}_{table}_{action}".format(host=event["host"], schema=event["schema"],
                                                                       table=event["table"], action=event["action"])
                jobs = event2jobs[event_type]
                for job in jobs:
                    if event["action"] not in job["actions"]:
                        continue

                    watched = job.get("watched")
                    if watched:
                        func_name, kwargs = watched.items()[0]
                        func = getattr(row_filters, func_name)
                        is_ok = func(event, **kwargs)
                        if not is_ok:
                            continue

                    pipeline = job["pipeline"]
                    rows = do_pipeline(pipeline, event["values"])
                    dest = job["dest"]
                    if isinstance(dest, list):
                        for d in dest:
                            to_dest(d, rows)
                    else:
                        to_dest(dest, rows)
                logging.info(json.dumps(event, cls=DateEncoder))
                cache.set_log_pos(binlogevent.packet.log_pos)


if __name__ == "__main__":
    # sys.argv = ["./config/example_binlog.py"]
    config_path = sys.argv[-1]
    config_module = importlib.import_module(
        ".".join(config_path[:-3].split("/")[-2:]),
        "config"
    )

    if config_module.STREAM == "INIT":
        handle_init_stream(config_module)
    elif config_module.STREAM == "BINLOG":
        handle_binlog_stream(config_module)
