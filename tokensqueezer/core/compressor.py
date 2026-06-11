"""
压缩引擎基类和调度器

提供压缩器的抽象基类、压缩结果数据模型和压缩引擎调度器。
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from rich.console import Console

from .content_detector import ContentDetector, ContentType
from .token_counter import TokenCounter

console = Console()


@dataclass
class CompressionResult:
    """压缩结果数据类

    Attributes:
        original_text: 原始文本
        compressed_text: 压缩后的文本
        original_tokens: 原始Token数量
        compressed_tokens: 压缩后Token数量
        ratio: 压缩率（0-1，越小表示压缩越多）
        saved_tokens: 节省的Token数量
        elapsed_time: 压缩耗时（秒）
        content_type: 内容类型
        compressor_name: 使用的压缩器名称
    """

    original_text: str
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    ratio: float
    saved_tokens: int
    elapsed_time: float
    content_type: ContentType = ContentType.TEXT
    compressor_name: str = ""

    @property
    def compression_percentage(self) -> float:
        """压缩百分比（节省的Token占比）"""
        if self.original_tokens == 0:
            return 0.0
        return (self.saved_tokens / self.original_tokens) * 100

    def summary(self) -> str:
        """生成压缩结果摘要"""
        return (
            f"压缩器: {self.compressor_name}\n"
            f"内容类型: {self.content_type.value}\n"
            f"原始Token: {self.original_tokens}\n"
            f"压缩后Token: {self.compressed_tokens}\n"
            f"节省Token: {self.saved_tokens} ({self.compression_percentage:.1f}%)\n"
            f"压缩率: {self.ratio:.2f}\n"
            f"耗时: {self.elapsed_time:.4f}s"
        )


class CompressorBase(ABC):
    """压缩器抽象基类

    所有压缩器必须继承此类并实现 compress 方法。
    """

    # 压缩器名称
    name: str = "base"
    # 支持的内容类型
    supported_types: list = [ContentType.TEXT]
    # 压缩器描述
    description: str = ""

    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """初始化压缩器

        Args:
            token_counter: Token计数器实例，如果为None则使用默认计数器
        """
        self._token_counter = token_counter or TokenCounter()

    @abstractmethod
    def compress(self, text: str, ratio: float = 0.5) -> str:
        """压缩文本

        Args:
            text: 待压缩的文本
            ratio: 目标压缩率（0.1-0.9），0.1表示最大压缩，0.9表示最小压缩

        Returns:
            压缩后的文本
        """
        ...

    def count_tokens(self, text: str) -> int:
        """计算文本的Token数量

        Args:
            text: 输入文本

        Returns:
            Token数量
        """
        return self._token_counter.count(text)

    def validate_ratio(self, ratio: float) -> float:
        """验证并修正压缩率

        Args:
            ratio: 目标压缩率

        Returns:
            修正后的压缩率（限制在0.1-0.9之间）
        """
        return max(0.1, min(0.9, ratio))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


class CompressionEngine:
    """压缩引擎调度器

    根据内容类型自动选择合适的压缩器进行压缩。
    """

    def __init__(
        self,
        compressors: Optional[list[CompressorBase]] = None,
        token_counter: Optional[TokenCounter] = None,
    ):
        """初始化压缩引擎

        Args:
            compressors: 自定义压缩器列表，如果为None则使用所有内置压缩器
            token_counter: 自定义Token计数器
        """
        self._token_counter = token_counter or TokenCounter()
        self._content_detector = ContentDetector()
        self._compressors: dict[ContentType, CompressorBase] = {}

        # 注册压缩器
        if compressors:
            for compressor in compressors:
                self.register_compressor(compressor)
        else:
            self._load_default_compressors()

    def _load_default_compressors(self) -> None:
        """加载所有内置压缩器"""
        from tokensqueezer.compressors.text import TextCompressor
        from tokensqueezer.compressors.json import JsonCompressor
        from tokensqueezer.compressors.code import CodeCompressor
        from tokensqueezer.compressors.markdown import MarkdownCompressor
        from tokensqueezer.compressors.log import LogCompressor

        default_compressors = [
            TextCompressor(self._token_counter),
            JsonCompressor(self._token_counter),
            CodeCompressor(self._token_counter),
            MarkdownCompressor(self._token_counter),
            LogCompressor(self._token_counter),
        ]

        for compressor in default_compressors:
            self.register_compressor(compressor)

    def register_compressor(self, compressor: CompressorBase) -> None:
        """注册压缩器

        Args:
            compressor: 压缩器实例
        """
        for content_type in compressor.supported_types:
            self._compressors[content_type] = compressor

    def get_compressor(self, content_type: ContentType) -> Optional[CompressorBase]:
        """获取指定内容类型的压缩器

        Args:
            content_type: 内容类型

        Returns:
            对应的压缩器实例，如果不存在则返回None
        """
        return self._compressors.get(content_type)

    def compress(
        self,
        text: str,
        content_type: Optional[ContentType] = None,
        ratio: float = 0.5,
    ) -> CompressionResult:
        """压缩文本

        Args:
            text: 待压缩的文本
            content_type: 指定内容类型，如果为None则自动检测
            ratio: 目标压缩率（0.1-0.9）

        Returns:
            CompressionResult 压缩结果

        Raises:
            ValueError: 当文本为空或不支持的内容类型时
        """
        if not text or not text.strip():
            raise ValueError("输入文本不能为空")

        # 自动检测内容类型
        if content_type is None:
            content_type = self._content_detector.detect(text)

        # 获取压缩器
        compressor = self.get_compressor(content_type)
        if compressor is None:
            raise ValueError(f"不支持的内容类型: {content_type}")

        # 计算原始Token数
        original_tokens = self._token_counter.count(text)

        # 执行压缩
        start_time = time.perf_counter()
        ratio = compressor.validate_ratio(ratio)
        compressed_text = compressor.compress(text, ratio=ratio)
        elapsed_time = time.perf_counter() - start_time

        # 计算压缩后Token数
        compressed_tokens = self._token_counter.count(compressed_text)

        # 计算压缩率
        if original_tokens > 0:
            actual_ratio = compressed_tokens / original_tokens
        else:
            actual_ratio = 1.0

        return CompressionResult(
            original_text=text,
            compressed_text=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            ratio=actual_ratio,
            saved_tokens=original_tokens - compressed_tokens,
            elapsed_time=elapsed_time,
            content_type=content_type,
            compressor_name=compressor.name,
        )

    def list_compressors(self) -> list[dict]:
        """列出所有已注册的压缩器

        Returns:
            压缩器信息列表
        """
        seen = set()
        result = []
        for ct, comp in self._compressors.items():
            if comp.name not in seen:
                seen.add(comp.name)
                result.append({
                    "name": comp.name,
                    "supported_types": [t.value for t in comp.supported_types],
                    "description": comp.description,
                })
        return result
