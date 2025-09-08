#!/usr/bin/env python3
"""
基于FastAPI的爬虫监控Web界面
"""

import os
import sys
import json
import sqlite3
import asyncio
import subprocess
import threading
import zipfile
import shutil
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from webspider.database import UrlDatabase

# 数据模型
class StatsResponse(BaseModel):
    total: int
    pending: int
    success: int
    failed: int
    crawling: int
    update_time: str

class PageInfo(BaseModel):
    url: str
    title: str
    html_file: Optional[str]
    crawled_time: Optional[str]
    file_exists: bool
    status: str

class FailedPage(BaseModel):
    url: str
    error: str
    time: Optional[str]

class SearchQuery(BaseModel):
    keyword: str
    limit: int = 50

class CrawlerConfig(BaseModel):
    start_urls: List[str]
    depth: int = 3
    workers: int = 2
    enable_js: bool = False

class CrawlerStatus(BaseModel):
    running: bool
    task: Optional[str]
    progress: Dict[str, int]
    current_urls: List[Dict[str, str]]

class FileStats(BaseModel):
    total: int
    total_size: int

class PackageResult(BaseModel):
    filename: str
    size: int
    file_count: int


# 全局配置
DATABASE_PATH = project_root / 'spider_urls.db'
WEBPAGES_DIR = project_root / 'webpages'
STATIC_DIR = Path(__file__).parent / 'static'
TEMPLATES_DIR = Path(__file__).parent / 'templates'

# 确保目录存在
WEBPAGES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)


# 后台监控任务（前向声明）
async def background_monitor():
    """后台监控任务"""
    pass  # 实际实现将在后面定义


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    print("爬虫监控系统启动中...")
    print(f"数据库路径: {DATABASE_PATH}")
    print(f"网页目录: {WEBPAGES_DIR}")
    print("访问地址: http://localhost:8000")
    
    # 启动后台监控任务
    monitor_task = asyncio.create_task(background_monitor_impl())
    
    yield
    
    # 关闭事件
    print("爬虫监控系统正在关闭...")
    # 取消后台任务
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass

# FastAPI应用
app = FastAPI(
    title="网页爬虫监控系统",
    description="实时监控爬虫抓取状态和浏览已抓取的网页",
    version="1.0.0",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class CrawlerController:
    """爬虫控制器"""
    
    def __init__(self):
        self.process = None
        self.running = False
        self.current_config = None
        self.websocket_connections = []
        
    def is_running(self):
        """检查爬虫是否正在运行"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    async def start_crawler(self, config: CrawlerConfig):
        """启动爬虫"""
        if self.is_running():
            raise HTTPException(status_code=400, detail="爬虫已在运行中")
        
        try:
            # 构建命令
            cmd = [
                sys.executable,
                str(project_root / "run_crawler.py"),
                "--workers", str(config.workers),
                "--depth", str(config.depth)
            ]
            
            # 添加起始URL
            for url in config.start_urls:
                cmd.extend(["--url", url])
            
            if config.enable_js:
                cmd.append("--enable-js")
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.running = True
            self.current_config = config
            
            # 启动日志监控线程
            log_thread = threading.Thread(target=self._monitor_logs, daemon=True)
            log_thread.start()
            
            # 启动进程监控线程
            monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
            monitor_thread.start()
            
            return {"message": "爬虫启动成功", "pid": self.process.pid}
            
        except Exception as e:
            self.running = False
            self.process = None
            raise HTTPException(status_code=500, detail=f"启动爬虫失败: {str(e)}")
    
    async def stop_crawler(self):
        """停止爬虫"""
        if not self.is_running():
            raise HTTPException(status_code=400, detail="爬虫未在运行")
        
        try:
            # 终止进程
            self.process.terminate()
            
            # 等待进程结束
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # 强制杀死进程
                self.process.kill()
                self.process.wait()
            
            self.running = False
            self.process = None
            self.current_config = None
            
            # 广播停止消息
            await self._broadcast_message({
                "type": "status_update",
                "data": {"running": False, "task": None}
            })
            
            return {"message": "爬虫已停止"}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"停止爬虫失败: {str(e)}")
    
    def get_status(self):
        """获取爬虫状态"""
        return {
            "running": self.is_running(),
            "task": f"抓取 {len(self.current_config.start_urls)} 个起始URL" if self.current_config else None,
            "progress": self._get_progress(),
            "current_urls": []
        }
    
    def _get_progress(self):
        """获取抓取进度"""
        try:
            # 使用新的PostgreSQL数据库
            from webspider.database import UrlDatabase
            from webspider.config import DatabaseConfig
            import psycopg2
            
            db = UrlDatabase()
            stats = db.get_stats()
            
            return {
                "total": stats.get('total', 0),
                "completed": stats.get('success', 0) + stats.get('failed', 0),
                "success": stats.get('success', 0),
                "pending": stats.get('pending', 0),
                "failed": stats.get('failed', 0),
                "crawling": stats.get('crawling', 0)
            }
        except Exception as e:
            print(f"获取进度失败: {e}")
            return {"total": 0, "completed": 0, "success": 0, "pending": 0, "failed": 0, "crawling": 0}
    
    def _monitor_logs(self):
        """监控日志输出"""
        if not self.process:
            return
        
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    line = line.strip()
                    if line:
                        # 确定日志级别
                        level = 'info'
                        if 'ERROR' in line.upper() or 'FAILED' in line.upper():
                            level = 'error'
                        elif 'WARNING' in line.upper() or 'WARN' in line.upper():
                            level = 'warning'
                        elif 'SUCCESS' in line.upper() or 'COMPLETED' in line.upper():
                            level = 'success'
                        
                        # 广播日志消息
                        asyncio.create_task(self._broadcast_message({
                            "type": "log",
                            "data": {"message": line, "level": level}
                        }))
        except Exception as e:
            print(f"日志监控错误: {e}")
    
    def _monitor_process(self):
        """监控进程状态"""
        while self.is_running():
            try:
                # 定期广播状态和进度
                asyncio.create_task(self._broadcast_status())
                time.sleep(2)  # 每2秒更新一次
            except Exception as e:
                print(f"进程监控错误: {e}")
                break
        
        # 进程结束，更新状态
        self.running = False
        self.process = None
        self.current_config = None
        
        asyncio.create_task(self._broadcast_message({
            "type": "status_update",
            "data": {"running": False, "task": None}
        }))
    
    async def add_websocket(self, websocket: WebSocket):
        """添加WebSocket连接"""
        self.websocket_connections.append(websocket)
    
    async def remove_websocket(self, websocket: WebSocket):
        """移除WebSocket连接"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
    
    async def _broadcast_message(self, message):
        """广播消息给所有WebSocket连接"""
        if not self.websocket_connections:
            return
        
        # 移除断开的连接
        active_connections = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
                active_connections.append(websocket)
            except:
                pass
        
        self.websocket_connections = active_connections
    
    async def _broadcast_status(self):
        """广播状态更新"""
        status = self.get_status()
        await self._broadcast_message({
            "type": "status_update",
            "data": {"running": status["running"], "task": status["task"]}
        })
        await self._broadcast_message({
            "type": "progress_update",
            "data": status["progress"]
        })


class FileManager:
    """文件管理器"""
    
    def __init__(self, webpages_dir: Path):
        self.webpages_dir = webpages_dir
        self.archives_dir = webpages_dir.parent / "archives"
        self.archives_dir.mkdir(exist_ok=True)
    
    def get_file_stats(self) -> FileStats:
        """获取文件统计信息"""
        try:
            html_files = list(self.webpages_dir.glob("*.html"))
            total_size = sum(f.stat().st_size for f in html_files if f.exists())
            
            return FileStats(
                total=len(html_files),
                total_size=total_size
            )
        except Exception as e:
            print(f"获取文件统计失败: {e}")
            return FileStats(total=0, total_size=0)
    
    async def package_files(self) -> PackageResult:
        """打包所有文件"""
        try:
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"webpages_archive_{timestamp}.zip"
            zip_path = self.archives_dir / zip_filename
            
            # 获取所有HTML文件和元数据文件
            files_to_archive = []
            files_to_archive.extend(self.webpages_dir.glob("*.html"))
            files_to_archive.extend(self.webpages_dir.glob("*.json"))
            
            if not files_to_archive:
                raise HTTPException(status_code=404, detail="没有可打包的文件")
            
            # 创建ZIP文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_archive:
                    if file_path.exists():
                        arcname = file_path.name
                        zipf.write(file_path, arcname)
            
            # 获取ZIP文件信息
            zip_size = zip_path.stat().st_size
            
            return PackageResult(
                filename=zip_filename,
                size=zip_size,
                file_count=len(files_to_archive)
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"打包文件失败: {str(e)}")
    
    async def clean_files(self) -> Dict[str, int]:
        """清理所有文件"""
        try:
            # 获取所有要删除的文件
            files_to_delete = []
            files_to_delete.extend(self.webpages_dir.glob("*.html"))
            files_to_delete.extend(self.webpages_dir.glob("*.json"))
            
            deleted_count = 0
            for file_path in files_to_delete:
                try:
                    if file_path.exists():
                        file_path.unlink()
                        deleted_count += 1
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")
            
            return {"deleted_count": deleted_count}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"清理文件失败: {str(e)}")
    
    def get_archive_path(self, filename: str) -> Path:
        """获取归档文件路径"""
        return self.archives_dir / filename


class SpiderMonitor:
    """爬虫监控类"""
    
    def __init__(self, db_path: Path, webpages_dir: Path):
        self.db_path = db_path  # 保留用于兼容性，但不再使用
        self.webpages_dir = webpages_dir
        
        # 使用新的PostgreSQL数据库连接
        try:
            self.db = UrlDatabase()
        except Exception as e:
            print(f"数据库连接失败: {e}")
            self.db = None
            
        self.websocket_connections: List[WebSocket] = []
        
    async def get_stats(self) -> StatsResponse:
        """获取统计信息"""
        if not self.db:
            return StatsResponse(
                total=0,
                pending=0,
                success=0,
                failed=0,
                crawling=0,
                update_time=datetime.now().isoformat()
            )
        
        stats = self.db.get_stats()
        return StatsResponse(
            total=stats['total'],
            pending=stats['pending'],
            success=stats['success'],
            failed=stats['failed'],
            crawling=stats['crawling'],
            update_time=datetime.now().isoformat()
        )
    
    async def get_recent_pages(self, limit: int = 20) -> List[PageInfo]:
        """获取最近抓取的页面"""
        if not self.db:
            return []
        
        try:
            from webspider.config import DatabaseConfig
            import psycopg2
            
            config = DatabaseConfig()
            with psycopg2.connect(**config.get_postgres_params()) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT url, title, html_file_path, crawled_time, status
                    FROM urls 
                    WHERE status = 'success'
                    ORDER BY crawled_time DESC 
                    LIMIT %s
                ''', (limit,))
                
                pages = []
                for row in cursor.fetchall():
                    url, title, html_file_path, crawled_time, status = row
                    
                    # 检查文件是否存在
                    file_exists = False
                    if html_file_path:
                        full_path = self.webpages_dir / Path(html_file_path).name
                        file_exists = full_path.exists()
                    
                    pages.append(PageInfo(
                        url=url,
                        title=title or '无标题',
                        html_file=Path(html_file_path).name if html_file_path else None,
                        crawled_time=crawled_time.isoformat() if crawled_time else None,
                        file_exists=file_exists,
                        status=status
                    ))
                
                cursor.close()
                return pages
        except Exception as e:
            print(f"获取页面列表失败: {e}")
            return []
    
    async def get_failed_pages(self, limit: int = 10) -> List[FailedPage]:
        """获取失败的页面"""
        if not self.db:
            return []
        
        try:
            from webspider.config import DatabaseConfig
            import psycopg2
            
            config = DatabaseConfig()
            with psycopg2.connect(**config.get_postgres_params()) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT url, error_message, crawled_time
                    FROM urls 
                    WHERE status = 'failed'
                    ORDER BY crawled_time DESC 
                    LIMIT %s
                ''', (limit,))
                
                result = [
                    FailedPage(
                        url=row[0],
                        error=row[1] or '未知错误',
                        time=row[2].isoformat() if row[2] else None
                    )
                    for row in cursor.fetchall()
                ]
                
                cursor.close()
                return result
        except Exception as e:
            print(f"获取失败页面失败: {e}")
            return []
    
    async def search_pages(self, keyword: str, limit: int = 50) -> List[PageInfo]:
        """搜索页面"""
        if not self.db:
            return []
        
        try:
            from webspider.config import DatabaseConfig
            import psycopg2
            
            config = DatabaseConfig()
            with psycopg2.connect(**config.get_postgres_params()) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT url, title, html_file_path, crawled_time, status
                    FROM urls 
                    WHERE (url ILIKE %s OR title ILIKE %s) AND status = 'success'
                    ORDER BY crawled_time DESC 
                    LIMIT %s
                ''', (f'%{keyword}%', f'%{keyword}%', limit))
                
                pages = []
                for row in cursor.fetchall():
                    url, title, html_file_path, crawled_time, status = row
                    
                    file_exists = False
                    if html_file_path:
                        full_path = self.webpages_dir / Path(html_file_path).name
                        file_exists = full_path.exists()
                    
                    pages.append(PageInfo(
                        url=url,
                        title=title or '无标题',
                        html_file=Path(html_file_path).name if html_file_path else None,
                        crawled_time=crawled_time.isoformat() if crawled_time else None,
                        file_exists=file_exists,
                        status=status
                    ))
                
                cursor.close()
                return pages
        except Exception as e:
            print(f"搜索页面失败: {e}")
            return []
    
    async def get_all_files(self, limit: int = 100) -> List[PageInfo]:
        """直接获取webpages目录中的所有HTML文件"""
        try:
            import os
            from datetime import datetime
            
            # 获取所有HTML文件
            html_files = [f for f in os.listdir(self.webpages_dir) if f.endswith('.html')]
            
            # 按修改时间排序
            html_files.sort(key=lambda f: os.path.getmtime(self.webpages_dir / f), reverse=True)
            
            pages = []
            for filename in html_files[:limit]:
                file_path = self.webpages_dir / filename
                if not file_path.exists():
                    continue
                
                # 获取文件信息
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                # 尝试从文件中提取标题
                title = '无标题'
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(5000)  # 只读前5000个字符
                        import re
                        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
                        if title_match:
                            title = title_match.group(1).strip()
                except:
                    pass
                
                # 尝试从PosgreSQL数据库中获取URL
                url = f"file://{filename}"
                if self.db:
                    try:
                        from webspider.config import DatabaseConfig
                        import psycopg2
                        
                        config = DatabaseConfig()
                        with psycopg2.connect(**config.get_postgres_params()) as conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                                SELECT url FROM urls 
                                WHERE html_file_path ILIKE %s
                                LIMIT 1
                            ''', (f'%{filename}%',))
                            result = cursor.fetchone()
                            if result:
                                url = result[0]
                            cursor.close()
                    except Exception as e:
                        print(f"查询数据库失败: {e}")
                
                pages.append(PageInfo(
                    url=url,
                    title=title,
                    html_file=filename,
                    crawled_time=mtime.isoformat(),
                    file_exists=True,
                    status='success'
                ))
            
            return pages
        except Exception as e:
            print(f"获取文件列表失败: {e}")
            return []
    
    async def add_websocket(self, websocket: WebSocket):
        """添加WebSocket连接"""
        self.websocket_connections.append(websocket)
    
    async def remove_websocket(self, websocket: WebSocket):
        """移除WebSocket连接"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
    
    async def broadcast_stats(self):
        """广播统计信息给所有连接的客户端"""
        if not self.websocket_connections:
            return
        
        stats = await self.get_stats()
        message = {
            "type": "stats_update",
            "data": stats.dict()
        }
        
        # 移除断开的连接
        active_connections = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_json(message)
                active_connections.append(websocket)
            except:
                pass
        
        self.websocket_connections = active_connections


# 创建监控实例
monitor = SpiderMonitor(DATABASE_PATH, WEBPAGES_DIR)

# 创建爬虫控制器实例
crawler_controller = CrawlerController()

# 创建文件管理器实例
file_manager = FileManager(WEBPAGES_DIR)

# 后台监控任务（实际实现）
async def background_monitor_impl():
    """后台监控任务实际实现"""
    last_stats = None
    
    while True:
        try:
            current_stats = await monitor.get_stats()
            
            # 如果统计信息有变化，推送给所有客户端
            if current_stats.dict() != (last_stats.dict() if last_stats else None):
                await monitor.broadcast_stats()
                last_stats = current_stats
            
            await asyncio.sleep(5)  # 每5秒检查一次
            
        except Exception as e:
            print(f"后台监控错误: {e}")
            await asyncio.sleep(10)


# API路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """主页"""
    try:
        with open(TEMPLATES_DIR / "index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>爬虫监控系统</title></head>
            <body>
                <h1>爬虫监控系统</h1>
                <p>前端页面正在加载中...</p>
                <p>请访问 <a href="/docs">/docs</a> 查看API文档</p>
            </body>
        </html>
        """)


@app.get("/chart_debug.html", response_class=HTMLResponse)
async def chart_debug():
    """图表调试页面"""
    try:
        debug_file_path = Path("chart_debug.html")
        if debug_file_path.exists():
            with open(debug_file_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            raise HTTPException(status_code=404, detail="调试页面未找到")
    except Exception as e:
        print(f"加载调试页面失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """获取统计信息"""
    return await monitor.get_stats()


@app.get("/api/pages", response_model=List[PageInfo])
async def get_pages(limit: int = Query(20, ge=1, le=100)):
    """获取页面列表"""
    return await monitor.get_recent_pages(limit)


@app.get("/api/failed", response_model=List[FailedPage])
async def get_failed_pages(limit: int = Query(10, ge=1, le=50)):
    """获取失败页面"""
    return await monitor.get_failed_pages(limit)


@app.get("/api/search", response_model=List[PageInfo])
async def search_pages(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=100)
):
    """搜索页面"""
    return await monitor.search_pages(q, limit)


@app.get("/api/files", response_model=List[PageInfo])
async def get_all_files(limit: int = Query(100, ge=1, le=200)):
    """获取webpages目录中的所有HTML文件"""
    return await monitor.get_all_files(limit)


# =============================================================================
# 爬虫控制API
# =============================================================================

@app.get("/crawler")
async def crawler_page():
    """爬虫配置页面"""
    try:
        with open(TEMPLATES_DIR / "crawler.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="页面不存在")


@app.post("/api/crawler/start")
async def start_crawler(config: CrawlerConfig):
    """启动爬虫任务"""
    return await crawler_controller.start_crawler(config)


@app.post("/api/crawler/stop")
async def stop_crawler():
    """停止爬虫任务"""
    return await crawler_controller.stop_crawler()


@app.get("/api/crawler/status", response_model=CrawlerStatus)
async def get_crawler_status():
    """获取爬虫状态"""
    status = crawler_controller.get_status()
    return CrawlerStatus(**status)


# =============================================================================
# 文件管理API
# =============================================================================

@app.get("/api/files/stats", response_model=FileStats)
async def get_file_stats():
    """获取文件统计信息"""
    return file_manager.get_file_stats()


@app.post("/api/files/package", response_model=PackageResult)
async def package_files():
    """打包所有文件"""
    return await file_manager.package_files()


@app.post("/api/files/clean")
async def clean_files():
    """清理所有文件"""
    return await file_manager.clean_files()


@app.get("/api/files/download-archive/{filename}")
async def download_archive(filename: str):
    """下载归档文件"""
    archive_path = file_manager.get_archive_path(filename)
    
    if not archive_path.exists():
        raise HTTPException(status_code=404, detail="归档文件不存在")
    
    return FileResponse(
        str(archive_path),
        media_type='application/zip',
        filename=filename
    )


@app.get("/api/view/{filename}")
async def view_page(filename: str):
    """查看HTML页面"""
    try:
        file_path = WEBPAGES_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查文件扩展名
        if not filename.endswith('.html'):
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        return FileResponse(str(file_path), media_type='text/html')
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"查看页面失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@app.get("/api/download/{filename}")
async def download_page(filename: str):
    """下载HTML页面"""
    try:
        file_path = WEBPAGES_DIR / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            str(file_path), 
            media_type='application/octet-stream',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"下载页面失败: {e}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


# WebSocket端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket连接端点"""
    await websocket.accept()
    await monitor.add_websocket(websocket)
    
    try:
        # 发送初始数据
        stats = await monitor.get_stats()
        pages = await monitor.get_recent_pages()
        
        await websocket.send_json({
            "type": "initial_data",
            "data": {
                "stats": stats.dict(),
                "pages": [page.dict() for page in pages]
            }
        })
        
        # 保持连接活跃
        while True:
            try:
                # 等待客户端消息
                data = await websocket.receive_json()
                
                if data.get("type") == "request_update":
                    # 客户端请求更新数据
                    stats = await monitor.get_stats()
                    pages = await monitor.get_recent_pages()
                    
                    await websocket.send_json({
                        "type": "data_update",
                        "data": {
                            "stats": stats.dict(),
                            "pages": [page.dict() for page in pages]
                        }
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket处理错误: {e}")
                break
                
    finally:
        await monitor.remove_websocket(websocket)


@app.websocket("/ws/crawler")
async def crawler_websocket_endpoint(websocket: WebSocket):
    """爬虫控制WebSocket连接端点"""
    await websocket.accept()
    await crawler_controller.add_websocket(websocket)
    
    try:
        # 发送初始状态
        status = crawler_controller.get_status()
        await websocket.send_json({
            "type": "status_update",
            "data": {"running": status["running"], "task": status["task"]}
        })
        await websocket.send_json({
            "type": "progress_update",
            "data": status["progress"]
        })
        
        # 发送文件统计
        file_stats = file_manager.get_file_stats()
        await websocket.send_json({
            "type": "file_stats",
            "data": file_stats.dict()
        })
        
        # 保持连接活跃
        while True:
            try:
                # 等待客户端消息
                data = await websocket.receive_json()
                
                if data.get("type") == "request_status":
                    # 客户端请求状态更新
                    status = crawler_controller.get_status()
                    await websocket.send_json({
                        "type": "status_update",
                        "data": {"running": status["running"], "task": status["task"]}
                    })
                    await websocket.send_json({
                        "type": "progress_update",
                        "data": status["progress"]
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"Crawler WebSocket处理错误: {e}")
                break
                
    finally:
        await crawler_controller.remove_websocket(websocket)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )