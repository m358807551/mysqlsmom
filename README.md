# mysqlsmom

简介：同步mysql数据到elasticsearch的工具；

## 特点

1. 纯Pythoo编写；
2. 有全量、增量更新两种模式；
3. 全量更新只占用少量内存；支持通过sql语句同步数据；
4. 增量更新自动断点续传；
5. 取自mysql的数据可经过一系列自定义函数的处理后再同步至elasticsearch；
6. 能用非常简单的配置完成复杂的同步任务；

## 环境

- python2.7；
- 如需增量同步，需要mysql开启binlog且本地开启redis；

## 简单示例

1. clone 项目到本地；

2. 安装依赖；

   ```
   cd mysqlsmom
   pip install -r requirements.txt
   ```

   默认支持 elasticsearch-2.4版本，支持其它版本请运行（将5.4换成需要的elasticsearch版本）

   ```
   pip install --upgrade elasticsearch==5.4
   ```

3. 编辑 ./config/example_init.py，按注释提示修改配置；

   ```python
   # coding=utf-8
   
   STREAM = "INIT"
   
   # 修改数据库连接
   CONNECTION = {
       'host': '127.0.0.1',
       'port': 3306,
       'user': 'root',
       'passwd': ''
   }
   
   # 修改elasticsearch节点
   NODES = [{"host": "127.0.0.1", "port": 9200}]
   
   TASKS = [
       {
           "stream": {
               "database": "test_db",  # 在此数据库执行sql语句
               "sql": "select * from person"  # 将该sql语句选中的数据同步到 elasticsearch
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
   ```

4. 运行

   ```
   cd mysqlsmom
   python mysqlsmom.py ./config/example_init.py
   ```

   等待同步完成即可；

## 未完待续

文档近期会不断完善，任何问题、建议都收到欢迎，请在issues提问，会在24小时内回复；
