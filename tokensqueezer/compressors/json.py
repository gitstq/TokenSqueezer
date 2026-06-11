"""
JSON压缩器

实现JSON数据的智能压缩，包括数组去重、字段裁剪、
值截断和嵌套结构优化。
"""

import json
from typing import Any, Optional

from tokensqueezer.core.compressor import CompressorBase
from tokensqueezer.core.content_detector import ContentType
from tokensqueezer.core.token_counter import TokenCounter


class JsonCompressor(CompressorBase):
    """JSON压缩器

    通过数组去重、字段裁剪、值截断和嵌套结构优化来压缩JSON数据。

    压缩率目标：50-80%
    """

    name: str = "json"
    supported_types: list = [ContentType.JSON]
    description: str = "JSON压缩器 - 字段裁剪、数组去重"

    # 默认保留的字段名（优先级高）
    PRIORITY_FIELDS = {"id", "name", "type", "status", "error", "code", "message"}

    # 低信息量字段（优先移除）
    LOW_INFO_FIELDS = {
        "timestamp", "created_at", "updated_at", "metadata",
        "trace_id", "request_id", "correlation_id", "version",
    }

    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """初始化JSON压缩器"""
        super().__init__(token_counter)

    def compress(self, text: str, ratio: float = 0.5) -> str:
        """压缩JSON文本

        执行以下压缩步骤：
        1. 解析JSON
        2. 数组去重
        3. 字段裁剪
        4. 值截断
        5. 序列化输出

        Args:
            text: JSON格式的文本
            ratio: 目标压缩率（0.1-0.9）

        Returns:
            压缩后的JSON文本
        """
        if not text or not text.strip():
            return ""

        ratio = self.validate_ratio(ratio)

        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError) as e:
            # 如果解析失败，返回原始文本
            return text

        # 执行压缩
        compressed = self._compress_value(data, ratio)

        # 序列化（紧凑格式）
        return json.dumps(compressed, ensure_ascii=False, separators=(',', ':'))

    def _compress_value(self, value: Any, ratio: float) -> Any:
        """递归压缩JSON值

        Args:
            value: JSON值
            ratio: 目标压缩率

        Returns:
            压缩后的值
        """
        if isinstance(value, dict):
            return self._compress_object(value, ratio)
        elif isinstance(value, list):
            return self._compress_array(value, ratio)
        elif isinstance(value, str):
            return self._compress_string(value, ratio)
        return value

    def _compress_object(self, obj: dict, ratio: float) -> dict:
        """压缩JSON对象

        根据压缩率决定是否裁剪低信息量字段。

        Args:
            obj: JSON对象
            ratio: 目标压缩率

        Returns:
            压缩后的对象
        """
        if not obj:
            return obj

        compressed = {}

        for key, value in obj.items():
            # 高压缩率时移除低信息量字段
            if ratio < 0.4 and key in self.LOW_INFO_FIELDS:
                continue

            # 压缩值
            compressed[key] = self._compress_value(value, ratio)

        return compressed

    def _compress_array(self, arr: list, ratio: float) -> list:
        """压缩JSON数组

        执行去重和相似项合并。

        Args:
            arr: JSON数组
            ratio: 目标压缩率

        Returns:
            压缩后的数组
        """
        if not arr:
            return arr

        # 去重（基于字符串表示）
        if ratio < 0.7:
            seen: list[str] = []
            unique: list[Any] = []
            for item in arr:
                item_str = json.dumps(item, ensure_ascii=False, sort_keys=True)
                if item_str not in seen:
                    seen.append(item_str)
                    unique.append(item)
            arr = unique

        # 限制数组长度（高压缩率时）
        max_length = self._get_max_array_length(ratio)
        if len(arr) > max_length:
            # 保留首尾元素
            if max_length >= 2:
                arr = arr[:max_length - 1] + [arr[-1]]
            else:
                arr = arr[:max_length]

        # 递归压缩每个元素
        return [self._compress_value(item, ratio) for item in arr]

    def _compress_string(self, text: str, ratio: float) -> str:
        """压缩字符串值

        对长字符串进行智能截断。

        Args:
            text: 字符串值
            ratio: 目标压缩率

        Returns:
            压缩后的字符串
        """
        if not text:
            return text

        # 根据压缩率确定最大长度
        max_length = self._get_max_string_length(ratio)

        if len(text) <= max_length:
            return text

        # 智能截断（保留首尾）
        if max_length > 20:
            keep_start = int(max_length * 0.7)
            keep_end = max_length - keep_start - 3
            return text[:keep_start] + "..." + text[-keep_end:]
        else:
            return text[:max_length]

    def _get_max_array_length(self, ratio: float) -> int:
        """根据压缩率获取数组最大长度

        Args:
            ratio: 目标压缩率

        Returns:
            数组最大长度
        """
        if ratio < 0.2:
            return 3
        elif ratio < 0.4:
            return 5
        elif ratio < 0.6:
            return 10
        elif ratio < 0.8:
            return 20
        return 50

    def _get_max_string_length(self, ratio: float) -> int:
        """根据压缩率获取字符串最大长度

        Args:
            ratio: 目标压缩率

        Returns:
            字符串最大长度
        """
        if ratio < 0.2:
            return 50
        elif ratio < 0.4:
            return 100
        elif ratio < 0.6:
            return 200
        elif ratio < 0.8:
            return 500
        return 1000
