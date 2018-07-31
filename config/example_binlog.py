# coding=utf-8

STREAM = "BINLOG"  # "BINLOG" or "INIT"
SERVER_ID = 99
SLAVE_UUID = __name__

BINLOG_CONNECTION = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'passwd': ''
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
