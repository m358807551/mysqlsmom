![Alt text](https://github.com/m358807551/images/blob/master/images/mysqlsmom/mysqlsmom_red.png?raw=true)

## 简介

一个 同步 Mysql 数据到 Elasticsearch的工具，特色是支持分析 binlog 做实时增量同步，以及支持编写自定义逻辑处理数据后再同步到 es。

纯 Python 编写，运行 mysqlsmom 的唯三要求:

* python2.7
* redis
* *Mysql* 配置  *binlog-format=row*

中文文档地址：https://mysqlsmom.readthedocs.io/en/latest/

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
