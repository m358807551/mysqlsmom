![Alt text](https://github.com/m358807551/images/blob/master/images/MysqlsMom.jpeg?raw=true)

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

## 快速开始

### 全量同步MySql数据到es

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

### 增量同步MySql数据到es

1. 确保要增量同步的MySql数据库开启binlog，且本地开启redis(为了存储最后一次读到的binlog文件名及读到的位置。未来可能支持本地文件存储该信息。)

2. 下载项目到本地，且安装好依赖后，编辑 ./config/example_init.py，按**注释**提示修改配置；

   ```python
   # coding=utf-8
   
   STREAM = "BINLOG"
   SERVER_ID = 99  # 确保每个用于binlog同步的配置文件的SERVER_ID不同；
   SLAVE_UUID = __name__
   
   # 配置开启binlog权限的MySql连接
   BINLOG_CONNECTION = {
       'host': '127.0.0.1',
       'port': 3306,
       'user': 'root',
       'passwd': ''
   }
   
   # 配置es节点
   NODES = [{"host": "127.0.0.1", "port": 9200}]
   
   TASKS = [
       {
           "stream": {
               "database": "test_db",  # [table]所在的数据库
               "table": "person"  # 监控该表的binlog
           },
           "jobs": [
               {
                   "actions": ["insert", "update"],
                   "pipeline": [
                       {"only_fields": {"fields": ["id", "name", "age"]}},  # 只同步这些字段到es，注释掉该行则同步全部字段的值到es
                       {"set_id": {"field": "id"}}  # 设置es中文档_id的值取自 id(或根据需要更改)字段
                   ],
                   "dest": {
                       "es": {
                           "action": "upsert",
                           "index": "test_index",  # 设置 index
                           "type": "test",         # 设置 type
                           "nodes": NODES
                       }
                   }
               }
           ]
       }
   ]
   ```

3. 运行

   ```
   cd mysqlsmom
   python mysqlsmom.py ./config/example_binlog.py
   ```

   该进程会一直运行，实时同步新增和更改后的数据到elasticsearch；

   注意：第一次运行该进程时不会同步MySql中已存在的数据，从第二次运行开始，将接着上次同步停止时的位置继续同步；

   同步旧数据请看*全量同步MySql数据到es*；

## 未完待续

文档近期会不断完善，任何问题、建议都收到欢迎，请在issues留言，会在24小时内回复；
