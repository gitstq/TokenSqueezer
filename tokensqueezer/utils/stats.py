"""
统计工具

提供压缩操作的统计收集和报告功能。
"""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CompressionStats:
    """单次压缩统计

    Attributes:
        content_type: 内容类型
        compressor_name: 压缩器名称
        original_tokens: 原始Token数
        compressed_tokens: 压缩后Token数
        saved_tokens: 节省的Token数
        compression_percentage: 压缩百分比
        elapsed_time: 耗时（秒）
        timestamp: 时间戳
    """

    content_type: str = ""
    compressor_name: str = ""
    original_tokens: int = 0
    compressed_tokens: int = 0
    saved_tokens: int = 0
    compression_percentage: float = 0.0
    elapsed_time: float = 0.0
    timestamp: float = field(default_factory=time.time)


class StatsCollector:
    """统计收集器

    收集和管理压缩操作的统计数据，支持摘要报告和重置。
    """

    def __init__(self, max_history: int = 1000):
        """初始化统计收集器

        Args:
            max_history: 最大历史记录数
        """
        self._history: list[CompressionStats] = []
        self._max_history = max_history

    def add(self, stats: CompressionStats) -> None:
        """添加一条压缩统计记录

        Args:
            stats: 压缩统计
        """
        self._history.append(stats)

        # 限制历史记录数量
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def add_from_result(self, result) -> None:
        """从压缩结果添加统计记录

        Args:
            result: CompressionResult实例
        """
        stats = CompressionStats(
            content_type=result.content_type.value,
            compressor_name=result.compressor_name,
            original_tokens=result.original_tokens,
            compressed_tokens=result.compressed_tokens,
            saved_tokens=result.saved_tokens,
            compression_percentage=result.compression_percentage,
            elapsed_time=result.elapsed_time,
        )
        self.add(stats)

    @property
    def total_compressions(self) -> int:
        """总压缩次数"""
        return len(self._history)

    @property
    def total_tokens_saved(self) -> int:
        """总节省Token数"""
        return sum(s.saved_tokens for s in self._history)

    @property
    def total_original_tokens(self) -> int:
        """总原始Token数"""
        return sum(s.original_tokens for s in self._history)

    @property
    def average_compression_percentage(self) -> float:
        """平均压缩百分比"""
        if not self._history:
            return 0.0
        return sum(s.compression_percentage for s in self._history) / len(self._history)

    @property
    def average_elapsed_time(self) -> float:
        """平均耗时"""
        if not self._history:
            return 0.0
        return sum(s.elapsed_time for s in self._history) / len(self._history)

    def get_by_type(self, content_type: str) -> list[CompressionStats]:
        """按内容类型获取统计记录

        Args:
            content_type: 内容类型

        Returns:
            对应类型的统计记录列表
        """
        return [s for s in self._history if s.content_type == content_type]

    def get_summary(self) -> dict:
        """获取统计摘要

        Returns:
            统计摘要字典
        """
        return {
            "total_compressions": self.total_compressions,
            "total_tokens_saved": self.total_tokens_saved,
            "total_original_tokens": self.total_original_tokens,
            "average_compression_percentage": round(self.average_compression_percentage, 2),
            "average_elapsed_time": round(self.average_elapsed_time, 6),
            "by_type": self._get_type_summary(),
        }

    def _get_type_summary(self) -> dict[str, dict]:
        """按类型获取统计摘要

        Returns:
            按类型分组的统计摘要
        """
        type_stats: dict[str, list[CompressionStats]] = {}
        for s in self._history:
            if s.content_type not in type_stats:
                type_stats[s.content_type] = []
            type_stats[s.content_type].append(s)

        result = {}
        for ct, stats in type_stats.items():
            result[ct] = {
                "count": len(stats),
                "total_saved": sum(s.saved_tokens for s in stats),
                "avg_compression": round(
                    sum(s.compression_percentage for s in stats) / len(stats), 2
                ),
            }

        return result

    def reset(self) -> None:
        """重置所有统计数据"""
        self._history = []

    @property
    def history(self) -> list[CompressionStats]:
        """获取历史记录"""
        return list(self._history)
