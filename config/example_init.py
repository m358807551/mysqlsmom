# coding=utf-8

STREAM = "INIT"

# 修改数据库连接
CONNECTION = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'passwd': ''
}

# 一次同步 BULK_SIZE 条数据到elasticsearch，不设置该配置项默认为1
BULK_SIZE = 1

# 修改elasticsearch节点
NODES = [{"host": "127.0.0.1", "port": 9200}]

TASKS = [
    {
        "stream": {
            "database": "test_db",  # 在此数据库执行sql语句
            "sql": "select * from person",  # 将该sql语句选中的数据同步到 elasticsearch
            # "pk": {"field": "id", "type": "char"}  # 当主键id的类型是字符串时
        },
        "jobs": [
            {
                "actions": ["insert", "update"],
                "pipeline": [
                    {"set_id": {"field": "id"}}  # 默认设置 id字段的值 为elasticsearch中的文档id
                ],
                "dest": {
                    "es": {
                        "action": "upsert",
                        "index": "test_index",   # 设置 index
                        "type": "test",          # 设置 type
                        "nodes": NODES
                    }
                }
            }
        ]
    }
]
