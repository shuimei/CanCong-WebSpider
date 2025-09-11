# CanCong-WebSpider 🕷️
![](docs/images/webspider.png)
一个现代化的智能网页爬虫系统，专为高效抓取和管理网页内容而设计。

## ✨ 主要特性

### 🚀 核心功能
- **智能抓取**：基于Scrapy框架的高性能网页抓取
- **JavaScript支持**：集成Selenium实现动态页面渲染
- **数据库存储**：PostgreSQL数据库存储URL状态，支持大规模数据处理
- **多进程并发**：支持1-10个worker并发抓取，提高效率
- **内容过滤**：智能关键词过滤，专注目标领域内容
- **数据迁移**：支持从SQLite平滑迁移到PostgreSQL
- **自动调度**：智能调度器自动随机启动新任务
- **简单抓取**：轻量级爬虫仅抓取指定URL，不递归
- **JS渲染选项**：可选择启用JavaScript渲染支持动态内容
- **优化性能**：复用WebDriver实例提高JS渲染性能
- **智能检测**：自动检测网页是否需要JS渲染
- **URL收集**：只收集URL不下载网页内容

### 🎯 Web监控界面
- **实时监控**：WebSocket实时推送抓取状态和进度
- **可视化仪表板**：Chart.js图表展示统计数据
- **在线配置**：Web界面配置抓取参数和启动任务
- **文件管理**：在线预览、下载和打包抓取结果
- **日志查看**：实时查看抓取日志和错误信息

### 🛠️ 内容处理
- **HTML清洗**：自动提取网页核心内容
- **Markdown转换**：HTML转Markdown格式
- **文件归档**：ZIP压缩打包抓取结果
- **重复清理**：自动清理重复文件

## 🏗️ 技术架构

```
CanCong-WebSpider/
├── webspider/              # 核心爬虫模块
│   ├── spiders/           # 爬虫实现
│   ├── middlewares.py     # 中间件
│   ├── pipelines.py       # 数据管道
│   ├── database.py        # 数据库操作
│   └── settings.py        # 配置文件
├── frontend/              # Web前端
│   ├── templates/         # HTML模板
│   ├── static/           # 静态资源
│   └── main.py           # FastAPI服务器
├── scripts/              # 工具脚本
│   ├── html_cleaner.py   # HTML清洗
│   ├── archive_webpages.py # 文件归档
│   └── clean_duplicates.py # 重复清理
├── webpages/             # 抓取结果存储
├── archives/             # 归档文件
└── mdpages/              # Markdown文件
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PostgreSQL 9.6+ (或可访问的PostgreSQL数据库服务器)
- Chrome/Chromium 浏览器（用于JavaScript渲染）

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/shuimei/CanCong-WebSpider.git
cd CanCong-WebSpider

# 安装Python依赖
pip install -r requirements.txt

# 配置PostgreSQL连接
# 创建.env文件并配置PostgreSQL连接信息
cp .env.example .env
# 编辑.env文件，填入PostgreSQL连接信息

# 执行数据库迁移（如果从旧版本升级）
python migrate_to_postgresql.py
```

### 基本使用

#### 1. 命令行抓取

```bash
# 抓取单个网站
python run_spider.py https://example.com

# 多进程抓取
python run_crawler.py --url https://example.com --workers 4 --depth 3

# 启用JavaScript渲染
python run_crawler.py --url https://example.com --enable-js

# 自动调度抓取（随机选择URL并自动启动新任务）
python scripts/auto_scheduler.py --batch-size 3 --workers 2 --depth 3

# 简单抓取（仅抓取指定URL，不递归）
python scripts/simple_crawler.py --limit 10 --workers 5

# 简单抓取（启用JavaScript渲染）
python scripts/simple_crawler_js.py --limit 5 --workers 3 --enable-js

# 优化抓取（复用WebDriver实例提高JS渲染性能）
python scripts/optimized_crawler_js.py --limit 10 --workers 5 --js-workers 2 --enable-js

# 智能抓取（自动检测是否需要JS渲染）
python scripts/smart_crawler.py --limit 10 --workers 5 --js-workers 2

# URL收集（只收集URL，不下载网页内容）
python scripts/url_collector.py --url https://example.com --depth 3
```

#### 2. Web界面使用

```bash
# 启动Web监控系统
cd frontend
python main.py
```

访问 http://localhost:8000 打开监控界面

- **监控台**: 查看抓取统计和历史记录
- **抓取配置**: 在线配置和启动抓取任务

### 配置参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--workers` | 并发进程数 | 2 |
| `--depth` | 抓取深度 | 3 |
| `--delay` | 请求延迟(秒) | 2 |
| `--enable-js` | 启用JavaScript渲染 | False |
| `--output` | 输出目录 | webpages |
| `--batch-size` | 自动调度每批URL数 | 2 |
| `--limit` | 简单抓取URL数量限制 | 100 |
| `--js-workers` | JS渲染工作线程数 | 2 |
| `--disable-js-detection` | 禁用JS需求检测 | False |

## 📊 功能演示

### Web监控界面

![监控台](docs/images/dashboard.png)
*实时监控抓取状态和统计数据*

![配置界面](docs/images/crawler.png)
*在线配置抓取参数*

### 命令行工具

```bash
# 查看抓取统计
python run_spider.py --stats

# 清理异常任务
python run_spider.py --clean

# HTML转Markdown
python scripts/html_cleaner.py

# 归档文件
python scripts/archive_webpages.py --delete --yes

# 自动调度器统计
python scripts/auto_scheduler.py --stats

# 简单爬虫统计
python scripts/simple_crawler.py --stats

# 简单爬虫统计（JS渲染版本）
python scripts/simple_crawler_js.py --stats

# 优化爬虫统计（JS渲染版本）
python scripts/optimized_crawler_js.py --stats

# 智能爬虫统计
python scripts/smart_crawler.py --stats

# URL收集器统计
python scripts/url_collector.py --stats
```

## 🎛️ 高级配置

### 数据库配置

系统使用PostgreSQL存储URL状态和抓取数据，支持高并发和大规模数据处理。

#### PostgreSQL配置

在`.env`文件中配置数据库连接信息：

```bash
PG_IP = "your-postgres-host"
PG_PORT = "5432"
PG_USERNAME = "your-username"
PG_PASSWORD = "your-password"
PG_DATABASE = "webspider"
```

#### 数据库迁移

如果从SQLite版本升级，可使用内置迁移脚本：

```bash
# 执行数据迁移
python migrate_to_postgresql.py

# 测试数据库连接
python test_postgresql_integration.py
```

### 内容过滤

在 `webspider/pipelines.py` 中配置关键词过滤规则：

```python
KEYWORDS = [
    "矿山", "地质", "自然资源", "安全监察"
    # 添加更多关键词...
]
```

### WebSocket实时通信

系统支持WebSocket实时推送：
- 抓取进度更新
- 状态变化通知
- 错误日志推送

## 📁 文件结构说明

- `webpages/`: 存储抓取的HTML文件
- `mdpages/`: 存储转换的Markdown文件
- `archives/`: 存储ZIP归档文件
- `PostgreSQL数据库`: 存储URL状态和元数据
- `.env`: PostgreSQL连接配置文件

## 🔧 开发指南

### 添加新的爬虫

1. 在 `webspider/spiders/` 目录创建新爬虫文件
2. 继承 `WebSpider` 基类
3. 实现 `parse` 方法

### 自定义中间件

1. 在 `webspider/middlewares.py` 添加中间件类
2. 在 `settings.py` 中注册中间件

### 扩展数据管道

1. 在 `webspider/pipelines.py` 添加管道类
2. 实现 `process_item` 方法

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建feature分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 开源协议

本项目采用 [Apache License 2.0](LICENSE) 开源协议。

### 许可证摘要

- ✅ **商业使用**：允许商业使用
- ✅ **修改**：允许修改源码
- ✅ **分发**：允许分发
- ✅ **专利使用**：提供明确的专利许可
- ✅ **私人使用**：允许私人使用
- ⚠️ **商标使用**：不授予商标权
- ⚠️ **责任**：不承担责任
- ⚠️ **保证**：不提供保证

使用本项目时，请保留原始的版权声明和许可证文本。

### 版权声明

```
Copyright 2024 CanCong-WebSpider Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

## 🙏 致谢

- [Scrapy](https://scrapy.org/) - 强大的爬虫框架
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Bootstrap](https://getbootstrap.com/) - UI组件库
- [Chart.js](https://www.chartjs.org/) - 图表库

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [提交问题](https://github.com/shuimei/CanCong-WebSpider/issues)
- Email: [your-email@example.com]

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！