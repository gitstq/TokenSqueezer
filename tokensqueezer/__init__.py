"""
TokenSqueezer - 智能LLM Token压缩工具

提供核心API和便捷函数。
"""

from typing import Optional

from .core.compressor import CompressionEngine, CompressionResult, CompressorBase
from .core.content_detector import ContentDetector, ContentType
from .core.pipeline import CompressionPipeline
from .core.token_counter import TokenCounter

# 全局引擎实例
_engine: Optional[CompressionEngine] = None


def _get_engine() -> CompressionEngine:
    """获取或创建全局压缩引擎"""
    global _engine
    if _engine is None:
        _engine = CompressionEngine()
    return _engine


def compress(
    text: str,
    content_type: Optional[ContentType] = None,
    ratio: float = 0.5,
) -> CompressionResult:
    """压缩文本（便捷函数）

    Args:
        text: 待压缩的文本
        content_type: 指定内容类型，如果为None则自动检测
        ratio: 目标压缩率（0.1-0.9）

    Returns:
        CompressionResult 压缩结果

    Example:
        >>> from tokensqueezer import compress
        >>> result = compress("你的长文本...")
        >>> print(result.compressed_text)
        >>> print(f"节省了 {result.saved_tokens} tokens")
    """
    engine = _get_engine()
    return engine.compress(text, content_type=content_type, ratio=ratio)


def count_tokens(text: str, encoding: str = "cl100k_base") -> int:
    """计算文本的Token数量（便捷函数）

    Args:
        text: 输入文本
        encoding: tiktoken编码名称

    Returns:
        Token数量
    """
    counter = TokenCounter(encoding_name=encoding)
    return counter.count(text)


def detect_content_type(text: str, filename: Optional[str] = None) -> ContentType:
    """检测内容类型（便捷函数）

    Args:
        text: 输入文本
        filename: 可选的文件名

    Returns:
        检测到的内容类型
    """
    detector = ContentDetector()
    return detector.detect(text, filename=filename)


__version__ = "1.0.0"
__author__ = "gitstq"

__all__ = [
    "compress",
    "count_tokens",
    "detect_content_type",
    "CompressionEngine",
    "CompressionResult",
    "CompressorBase",
    "CompressionPipeline",
    "ContentDetector",
    "ContentType",
    "TokenCounter",
]
