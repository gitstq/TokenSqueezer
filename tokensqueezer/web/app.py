"""
FastAPI应用工厂

创建和配置FastAPI应用实例。
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .routes import create_router


def create_app() -> FastAPI:
    """创建FastAPI应用

    Returns:
        配置好的FastAPI应用实例
    """
    app = FastAPI(
        title="TokenSqueezer",
        description="智能LLM Token压缩工具 - Web面板",
        version="1.0.0",
    )

    # 注册API路由
    api_router = create_router()
    app.include_router(api_router, prefix="/api")

    # 注册首页路由
    @app.get("/", response_class=HTMLResponse)
    async def index():
        """返回Web面板HTML"""
        templates_dir = Path(__file__).parent / "templates"
        index_file = templates_dir / "index.html"
        if index_file.exists():
            return index_file.read_text(encoding="utf-8")
        return "<h1>TokenSqueezer Web Panel</h1><p>Template not found</p>"

    return app
