# 桌面端全文文件检索系统
基于 PyQt6 + Elasticsearch + Redis + Docker 的多格式文件全文检索工具
点点star 
点点star
点点star
点点star


## 📖 项目介绍
本项目是基于 PyQt6 + Elasticsearch + Redis + Docker 开发的桌面端全文文件检索系统。支持 PDF、Word、PPT、TXT 多格式文档自动解析、目录递归爬取、建立全文索引；基于 Elasticsearch 实现全文检索、关键词高亮、模糊匹配、分页查询；使用 Redis 做搜索结果缓存，提升重复查询响应速度；通过 Watchdog 实现文件夹实时监控，文件新增 / 修改 / 删除自动同步更新索引；整套 Elasticsearch、Redis 中间件基于 Docker Compose 容器化一键部署，环境统一、开箱即用。前端基于 PyQt6 搭建可视化 GUI 界面，支持手动索引、全盘索引、目录监控、关键词搜索、结果预览、文件一键打开等完整功能。

## 🚀 项目启动
启动中间件 docker
docker-compose up -d

安装依赖
pip install -r requirements.txt

运行界面
python main.py

## 📌 配套知识点文档
https://blog.csdn.net/qq_58358642/article/details/161058620?sharetype=blogdetail&sharerId=161058620&sharerefer=PC&sharesource=qq_58358642&spm=1011.2480.3001.8118

## 📁 项目框架
```text
F:/tools/
├── docker-compose.yml        # ES + Redis 容器配置
├── requirements.txt          # Python 依赖
├── config.py                 # 配置参数
├── main.py                   # 程序入口
├── core/
│   ├── indexer.py            # 文件索引器
│   ├── searcher.py           # 搜索器
│   ├── file_monitor.py       # 文件监控
│   └── file_parser/          # 文件解析器
│       ├── pdf_parser.py
│       ├── word_parser.py
│       ├── ppt_parser.py
│       └── txt_parser.py
├── storage/
│   ├── elasticsearch_client.py
│   └── redis_client.py
└── gui/
