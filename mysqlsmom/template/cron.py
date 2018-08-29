# coding=utf-8

STREAM = "CRON"

# 修改数据库连接
CONNECTION = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'passwd': ''
}

# redis存储上次同步时间等信息
REDIS = {
    "host": "127.0.0.1",
    "port": 6379,
    "db": 0,
    "password": "password",  # 不需要密码则注释或删掉该行
}

# 一次同步 BULK_SIZE 条数据到elasticsearch，不设置该配置项默认为1
BULK_SIZE = 1

# 修改elasticsearch节点
NODES = [{"host": "127.0.0.1", "port": 9200}]

TASKS = [
    {
        "stream": {
            "database": "test_db",  # 在此数据库执行sql语句
            "sql": "select id, name from person where update_time >= ?",  # 将该sql语句选中的数据同步到 elasticsearch
            "seconds": 10,  # 每隔 seconds 秒同步一次,
            "init_time": "2018-08-15 18:05:47"  # 只有第一次同步会加载
        },
        "jobs": [
            {
                "pipeline": [
                    {"set_id": {"field": "id"}}  # 默认设置 id字段的值 为elasticsearch中的文档id
                ],
                "dest": {
                    "es": {
                        "action": "upsert",
                        "index": "test_index",   # 设置 index
                        "type": "test"          # 设置 type
                    }
                }
            }
        ]
    }
]

# CUSTOM_ROW_HANDLERS = "./my_handlers.py"
# CUSTOM_ROW_FILTERS = "./my_filters.py"
