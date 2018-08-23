# coding=utf-8

STREAM = "BINLOG"  # "BINLOG" or "INIT"
SERVER_ID = 99
SLAVE_UUID = __name__

# 一次同步 BULK_SIZE 条数据到elasticsearch，不设置该配置项默认为1
BULK_SIZE = 1

BINLOG_CONNECTION = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'passwd': ''
}

# redis存储上次同步位置等信息
REDIS = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0,
    "password": "your password",  # 不需要密码则注释或删掉该行
}


NODES = [{"host": "127.0.0.1", "port": 9200}]

TASKS = [
    {
        "stream": {
            "database": "test_db",
            "table": "person"
        },
        "jobs": [
            {
                "actions": ["insert", "update"],
                "pipeline": [
                    {"only_fields": {"fields": ["id", "name", "age"]}},
                    {"set_id": {"field": "id"}}
                ],
                "dest": {
                    "es": {
                        "action": "upsert",
                        "index": "test_index",
                        "type": "test",
                        "nodes": NODES
                    }
                }
            }
        ]
    }
]
