![Alt text](https://github.com/m358807551/images/blob/master/images/mysqlsmom/mysqlsmom_red.png?raw=true)

## 简介

一个 同步 Mysql 数据到 Elasticsearch的工具，特色是支持分析 binlog 做实时增量同步，以及支持编写自定义逻辑处理数据后再同步到 es。

纯 Python 编写，运行 mysqlsmom 的唯三要求:

* python2.7
* redis
* *Mysql* 配置  *binlog-format=row*

## 快速开始

从一个全量同步开始。

### 安装

```shell
pip install mysqlsmom
```

然后指定 elasticsearch 版本（默认支持2.4），支持其它版本请运行（将5.4换成需要的elasticsearch版本）

```shell
pip install --upgrade elasticsearch==5.4
```

### 设置同步配置

创建全量同步配置文件

```shell
mom new test_mom/init_config.py -t init --force
```

此时的目录结构

```shell
└── test_mom
    └── init_config.py
```

编辑同步配置

```shell
vim ./test_mom/init_config.py  # 按注释提示修改配置
```

### 开始同步

```
mom run -c ./test_mom/init_config.py
```

等待同步完成即可。

### 注意

全量同步完成后不会自动增量同步新修改的数据，需要增量同步请查看全部文档中的增量同步部分。

## 版本升级

本次更新只是加入了对 pip install mysqlsmom 以及 命令行的支持，关键代码并无任何改动。

通过旧版本 git clone 和 python mysqlsmom.py ./config/xxx.py 运行同步的用户 **无需** 更新代码，稍后加入对升级步骤的详细说明。

## 增量同步

### 分析 *binlog* 的增量同步

1. 确保要增量同步的MySql数据库开启binlog，且开启redis(为了存储最后一次读到的binlog文件名及读到的位置。未来可能支持本地文件存储该信息。)

2. 新建配置文件

   ```shell
   mom new test_mom/binlog_config.py -t binlog --force
   ```

3. 编辑 test_mom/binlog_config.py，按**注释**提示修改配置；

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

4. 运行

   ```shell
   mom run -c ./test_mom/binlog_config.py
   ```

   该进程会一直运行，实时同步新增和更改后的数据到elasticsearch；

   注意：第一次运行该进程时不会同步MySql中已存在的数据，从第二次运行开始，将接着上次同步停止时的位置继续同步；

   同步旧数据请看*全量同步MySql数据到es*；

### 基于更新时间的增量同步

若 *Mysql* 表中有类似 `update_time` 的时间字段，且在每次插入、更新数据后将该字段的值设置为操作时间，则可在不用开启 *binlog* 的情况下进行增量同步。

1. 新建配置文件

   ```
   mom new test_mom/cron_config.py -t cron --force
   ```

2. 编辑 test_mom/cron_config.py，按**注释**提示修改配置；

   ```python
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
                       {"set_id": {"field": "id"}}  # 默认设置 id字段的值 为 es 中的文档id
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
   ```

3. 运行

   ```shell
   mom run -c ./test_mom/cron_config.py
   ```

## 组织架构
![Alt text](https://github.com/m358807551/images/blob/master/images/mysqlsmom/all.png?raw=true)

## *Mysqlsmom* 使用实战

*Mysqlsmom* 的灵活性依赖于：

* 在 *row_handlers.py* 中添加自定义函数对取自Mysql的数据进行二次加工。
* 在 *row_filters.py* 中添加自定义函数决定是否要同步某一条数据。
* 在 *config/* 目录下的任意配置文件应用上面的函数。

如果不了解 Python 也没关系，上述两个文件中自带的函数足以应付大多数种情况，遇到特殊的同步需求可以在 Github 发起 issue 或通过微信、QQ联系作者。

### 同步多张表

在一个配置文件中即可完成：

```python
...
TASKS = [
    # 同步表1
    {
        "stream": {
            "database": "数据库名1",
            "table": "表名1"
        },
        "jobs": [...]
    }
    # 同步表2
    {
        "stream": {
            "database": "数据库名2",
            "table": "表名2"
        },
        "jobs": [...]
    }
]
```

一个 *Mysql Connection* 对应**一个**配置文件。

### 一张表同步到多个索引

分为两种情况。

一种是把相同的数据同步到不同的索引，配置如下：

```python
...
TASKS = [
    {
        "stream": {...},
        "jobs": [
            {
                "actions": [...],
                "pipeline": [...],
                "dest": [
                    # 同步到索引1
                    {
                        "es": {"action": "upsert", "index": "索引1", "type": "类型1", "nodes": NODES},
                    },
                    # 同步到索引2
                    {
                        "es": {"action": "upsert", "index": "索引2", "type": "类型2", "nodes": NODES},
                    }
                ]
            }
        ]
    },
    ...
]
```

另一种是把同一个表产生的数据经过不同的 *pipeline* 同步到不同的索引：

```python
...
TASKS = [
    {
        "stream": {...},
        "jobs": [
            {
                "actions": {...},
                "pipeline": [...],  # 对数据经过一系列处理
                "dest": {"es": {"index": "索引1", ...}}  # 同步到索引1
            },
            {
                "actions": {...},
                "pipeline": [...],  # 与上面的pipeline不同
                "dest": {"es": {"index": "索引2", ...}}  # 同步到索引2
            }
        ]
    }
]
```

* *TASKS* 中的每一项对应一张要同步的表。
* *jobs* 中的每一项对应对一条记录的一种处理方式。
* *dest* 中的每一项对应一个es索引类型。

### 只同步某些字段

对每条来自 *Mysql* 的 记录的处理都在 **pipeline** 中进行处理。

```python
"pipeline": [
  {"only_fields": {"fields": ["id", "name"]}},  # 只同步 id 和 name字段
    {"set_id": {"field": "id"}}  # 然后设置 id 字段为es中文档的_id
]
```

### 字段重命名

对于 *Mysql* 中的字段名和 *elasticsearch* 中的域名不一致的情况：

```python
"pipeline": [
    # 将name重命名为name1，age 重命名为age1
  {"replace_fields": {"name": ["name1"], "age": ["age1"]}},
    {"set_id": {"field": "id"}}
]
```

*pipeline* 会依次执行处理函数，上面的例子等价于：

```python
"pipeline": [
    # 先重命名 name 为 name1
  {"replace_fields": {"name": ["name1"]}},
    # 再重命名 age 为 age1
    {"replace_fields": {"age": ["age1"]}},
    {"set_id": {"field": "id"}}
]
```

还有一种特殊情形，es 中两个字段存相同的数据，但是分词方式不同。

例如 *name_default* 的分析器为 *default*，*name_raw* 设置为不分词，需要将 *name* 的值同时同步到这两个域：

```python
"pipeline": [
  {"replace_fields": {"name": ["name_default", "name_raw"]}},
    {"set_id": {"field": "id"}}
]
```

当然上述问题有一个更好的解决方案，在 *es* 的 *mappings* 中配置 *name* 字段的 *fields* 属性即可，这超出了本文档的内容。

### 切分字符串为数组

有时 Mysql 存储字符串类似："aaa|bbb|ccc"，希望转化成数组: ["aaa", "bbb", "ccc"] 再进行同步

```python
"pipeline": [
  # tags 存储类似"aaa|bbb|ccc"的字符串，将 tags 字段的值按符号 `|` 切分成数组
  {"split": {"field": "tags", "flag": "|"}},
    {"set_id": {"field": "id"}}
]
```

### 同步删除文档

只有 ***binlog* 同步** 能实现删除 *elasticsearch* 中的文档，配置如下：

```python
TASKS = [
    {
        "stream": {
            "database": "test_db",
            "table": "person"
        },
        "jobs": [
            # 插入、更新
            {
                "actions": ["insert", "update"],
                "pipeline": [
                    {"set_id": {"field": "id"}}  # 设置 id 字段的值为 es 中文档 _id
                ],
                "dest": {
                    "es": {
                        "action": "upsert",
                        ...
                    }
                }
            },
            # 重点在这里，配置删除
            {
                "actions": ["delete"],  # 当读取到 binlog 中该表的删除操作时
                "pipeline": [{"set_id": {"field": "id"}}],  # 要删除的文档 _id
                "dest": {
                    "es": {
                        "action": "delete",  # 在 es 中执行删除操作
                        ...  # 与上面的 index 和 type 相同
                    }
                }
            }
        ]
    },
    ...
]
```



### 更多示例正在更新

## 自定义处理函数

所有 row_handlers.py 文件里的函数都支持在 pipeline 里使用。

每一个同步任务都有一个 pipeline 配置，从 Mysql 取出的数据经过 pipeline 里的函数处理后传入es；每个处理函数的输入都是上一个处理函数的输出；

除此之外，可以自定义处理函数，以 binlog 同步为例：

1. 在同步配置文件的同一目录下创建文件：`my_handlers.py`
2. 修改同步的配置文件，取消倒数第二行 `# CUSTOM_ROW_HANDLERS = "./my_handlers.py"`的注释
3. 在`my_handlers.py`中编写自定义函数，写好的函数可以直接在 pipeline 中使用。

### 自定义函数的格式

`my_handlers.py `的文件内容按照如下格式

```python
# coding=utf-8
import copy

# 示例自定义函数，将 my_field 字段的值改为 my_value
def my_func(row, my_field, my_value):
    """
    参数 row: 这个参数一定要有，是一个字典，存储着行信息。示例：{"id": 123, "name": "啦啦啦"}
    参数 my_field: 在本例中期待传入要修改的字段名。示例：id, name
    参数 my_value: 将 my_field 的值设置为 my_value
    """
    new_row = copy.deepcopy(row) # 一定要有

    # 中间的处理逻辑，主要自定义这部分
    new_row[my_field] = my_value

    return new_row # 一定要有，返回处理后的结果，来交给接下来的处理函数，或者同步到es

# 自定义函数2，如果 _id 为空，就强行指定 _id 为 "123"
def my_func2(row):
    row = copy.deepcopy(row)
    if not row["_id"]:
        row["_id"] = "123"
    return row

# 自定义函数3...

```

然后可以直接在pipeline里使用了

```python
...
"pipeline": [
			    {
                    "my_func": # 刚刚自定义的函数名
                    # 自定义的参数
                    # 其中row参数 不用写
                    # 将所有的 name 字段的值 改为 "Jack"
                    {
                        "my_field": "name",
                        "my_value": "Jack"
                    }
                },
             	{"set_id": {"field": "id"}}  # 设置 id 字段的值为 es 中文档 _id
            ],
...
```



## 常见问题

#### 没有对应的 es 版本

```
pip install --upgrade elasticsearch==6.4.2
```

提示类似：

```
Could not find a version that satisfies the requirement elasticsearch==6.4.2 (from versions: 0.4.1, 0.4.2, 0.4.3, 0.4.4, 0.4.5, 1.0.0, 1.1.0, 1.1.1, 1.2.0, 1.3.0, 1.4.0, 1.5.0, 1.6.0, 1.7.0, 1.8.0, 1.9.0, 2.0.0, 2.1.0, 2.2.0, 2.3.0, 2.4.0, 2.4.1, 5.0.0, 5.0.1, 5.1.0, 5.2.0, 5.3.0, 5.4.0, 5.5.0, 5.5.1, 5.5.2, 5.5.3, 6.0.0, 6.1.1, 6.2.0, 6.3.0, 6.3.1)
No matching distribution found for elasticsearch==6.4.2
```

换较新的几个版本也兼容

```
pip install --upgrade elasticsearch==6.3.1
```

#### 安装出现问题

在虚拟环境安装，遇到的环境问题会变少

1. 准备
   ```
   pip install virtualenv
   ```

2. 当前目录创建虚拟环境
   ```
   virtualenv ./venv
   ```

3. 进入虚拟环境
   ```
   . ./venv/bin/activate
   ```

4. 安装 mysqlsmom
   ```
   pip install mysqlsmom
   pip install --upgrade elasticsearch==5.4  # 换成所需版本
   ```

5. 运行
   ```
   mom new ...
   ```

6. 退出虚拟环境
    ```
    deactivate
    ```

注意以后运行 mysqlsmom 都要进入虚拟环境


#### 为什么我的增量同步不及时？

1. 连接本地数据库增量同步不及时

   该情况暂未收到过反馈，如能复现请联系作者。

2. 连接线上数据库发现增量同步不及时

   2.1 推荐使用内网IP连接数据库。连接线上数据库（如开启在阿里、腾讯服务器上的Mysql）时，推荐使用内网IP地址，因为外网IP会受到带宽等限制导致获取binlog数据速度受限，最终可能造成同步延时。

## 待改进

1. 错误日志和稳定性有待提升；

## 未完待续

任何问题、建议都收到欢迎，请在issues留言，会在24小时内回复；或加入QQ群: 569069847；