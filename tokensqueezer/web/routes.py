"""
API路由定义

提供REST API端点：压缩文本、获取统计、健康检查。
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from tokensqueezer.core.compressor import CompressionEngine, CompressionResult
from tokensqueezer.core.content_detector import ContentType
from tokensqueezer.core.token_counter import TokenCounter

# 全局引擎实例
_engine = CompressionEngine()
_counter = TokenCounter()

# 历史记录
_history: list[dict] = []
_max_history = 100


class CompressRequest(BaseModel):
    """压缩请求模型"""
    text: str = Field(..., min_length=1, description="待压缩的文本")
    content_type: Optional[str] = Field(None, description="内容类型 (text/json/code/markdown/log)")
    ratio: float = Field(0.5, ge=0.1, le=0.9, description="目标压缩率 (0.1-0.9)")


class CompressResponse(BaseModel):
    """压缩响应模型"""
    original_tokens: int = Field(..., description="原始Token数量")
    compressed_tokens: int = Field(..., description="压缩后Token数量")
    ratio: float = Field(..., description="实际压缩率")
    saved_tokens: int = Field(..., description="节省的Token数量")
    compression_percentage: float = Field(..., description="节省百分比")
    elapsed_time: float = Field(..., description="压缩耗时(秒)")
    content_type: str = Field(..., description="内容类型")
    compressor: str = Field(..., description="使用的压缩器")
    compressed_text: str = Field(..., description="压缩后的文本")


class StatsResponse(BaseModel):
    """统计响应模型"""
    total_compressions: int = Field(..., description="总压缩次数")
    total_tokens_saved: int = Field(..., description="总节省Token数")
    average_compression: float = Field(..., description="平均压缩率")
    available_compressors: list[dict] = Field(..., description="可用压缩器列表")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    version: str = "1.0.0"


def create_router() -> APIRouter:
    """创建API路由器

    Returns:
        配置好的APIRouter实例
    """
    router = APIRouter()

    @router.post("/compress", response_model=CompressResponse)
    async def compress(request: CompressRequest) -> CompressResponse:
        """压缩文本

        接收文本内容，返回压缩结果。
        """
        try:
            # 解析内容类型
            content_type = None
            if request.content_type:
                try:
                    content_type = ContentType(request.content_type)
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"不支持的内容类型: {request.content_type}。"
                               f"支持的类型: {[t.value for t in ContentType]}"
                    )

            # 执行压缩
            result = _engine.compress(
                request.text,
                content_type=content_type,
                ratio=request.ratio,
            )

            # 记录历史
            _add_history(result)

            return CompressResponse(
                original_tokens=result.original_tokens,
                compressed_tokens=result.compressed_tokens,
                ratio=round(result.ratio, 4),
                saved_tokens=result.saved_tokens,
                compression_percentage=round(result.compression_percentage, 2),
                elapsed_time=round(result.elapsed_time, 6),
                content_type=result.content_type.value,
                compressor=result.compressor_name,
                compressed_text=result.compressed_text,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"压缩失败: {str(e)}")

    @router.get("/stats", response_model=StatsResponse)
    async def stats() -> StatsResponse:
        """获取压缩统计信息"""
        total_compressions = len(_history)
        total_saved = sum(h["saved_tokens"] for h in _history)

        if _history:
            avg_compression = sum(h["compression_percentage"] for h in _history) / len(_history)
        else:
            avg_compression = 0.0

        return StatsResponse(
            total_compressions=total_compressions,
            total_tokens_saved=total_saved,
            average_compression=round(avg_compression, 2),
            available_compressors=_engine.list_compressors(),
        )

    @router.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        """健康检查"""
        return HealthResponse(status="ok", version="1.0.0")

    @router.get("/history")
    async def history(limit: int = 20) -> list[dict]:
        """获取压缩历史记录"""
        return _history[-limit:]

    return router


def _add_history(result: CompressionResult) -> None:
    """添加压缩记录到历史

    Args:
        result: 压缩结果
    """
    record = {
        "original_tokens": result.original_tokens,
        "compressed_tokens": result.compressed_tokens,
        "saved_tokens": result.saved_tokens,
        "compression_percentage": round(result.compression_percentage, 2),
        "content_type": result.content_type.value,
        "compressor": result.compressor_name,
        "elapsed_time": round(result.elapsed_time, 6),
    }

    _history.append(record)

    # 限制历史记录数量
    if len(_history) > _max_history:
        _history.pop(0)
