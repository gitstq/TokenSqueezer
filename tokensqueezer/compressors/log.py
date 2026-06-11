"""
日志压缩器

实现日志的智能压缩，通过模式匹配去重、保留错误和警告、
时间戳标准化来大幅减少日志Token消耗。
"""

import re
from collections import Counter
from typing import Optional

from tokensqueezer.core.compressor import CompressorBase
from tokensqueezer.core.content_detector import ContentType
from tokensqueezer.core.token_counter import TokenCounter


class LogCompressor(CompressorBase):
    """日志压缩器

    通过模式匹配去重、保留重要日志级别、时间戳标准化来压缩日志。

    压缩率目标：60-90%
    """

    name: str = "log"
    supported_types: list = [ContentType.LOG]
    description: str = "日志压缩器 - 模式去重、保留关键信息"

    # 日志级别优先级（数字越大越重要）
    LOG_LEVEL_PRIORITY = {
        "trace": 0,
        "debug": 1,
        "info": 2,
        "warn": 3,
        "warning": 3,
        "error": 4,
        "critical": 5,
        "fatal": 5,
    }

    # 时间戳模式
    TIMESTAMP_PATTERNS = [
        re.compile(r'\d{4}[-/]\d{2}[-/]\d{2}[\sT]\d{2}:\d{2}:\d{2}(\.\d+)?'),
        re.compile(r'\d{2}:\d{2}:\d{2}(\.\d+)?'),
        re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'),
        re.compile(r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}'),
    ]

    # 日志级别提取模式
    LOG_LEVEL_PATTERN = re.compile(
        r'(?:\[(?:INFO|WARN|ERROR|DEBUG|TRACE|FATAL|CRITICAL|WARNING)\]|'
        r'(?:INFO|WARN|ERROR|DEBUG|TRACE|FATAL|CRITICAL|WARNING)\s*[-=:])',
        re.IGNORECASE
    )

    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """初始化日志压缩器"""
        super().__init__(token_counter)

    def compress(self, text: str, ratio: float = 0.5) -> str:
        """压缩日志文本

        执行以下压缩步骤：
        1. 解析日志行
        2. 时间戳标准化
        3. 模式去重
        4. 按级别过滤
        5. 重新组装

        Args:
            text: 日志文本
            ratio: 目标压缩率（0.1-0.9）

        Returns:
            压缩后的日志
        """
        if not text or not text.strip():
            return ""

        ratio = self.validate_ratio(ratio)
        lines = text.split('\n')

        # 解析日志行
        parsed_lines = [self._parse_log_line(line) for line in lines]

        # 步骤1：时间戳标准化
        if ratio < 0.8:
            parsed_lines = [self._normalize_timestamp(p) for p in parsed_lines]

        # 步骤2：模式去重
        deduped_lines = self._deduplicate_patterns(parsed_lines, ratio)

        # 步骤3：按级别过滤
        filtered_lines = self._filter_by_level(deduped_lines, ratio)

        # 重新组装
        result = '\n'.join(filtered_lines)

        if not result.strip():
            return text.strip()

        return result

    def _parse_log_line(self, line: str) -> dict:
        """解析单行日志

        Args:
            line: 日志行

        Returns:
            解析后的日志信息字典
        """
        result = {
            "original": line,
            "level": self._extract_log_level(line),
            "message": line,
            "has_timestamp": False,
        }

        # 检查是否包含时间戳
        for pattern in self.TIMESTAMP_PATTERNS:
            if pattern.search(line):
                result["has_timestamp"] = True
                break

        # 提取消息部分（移除时间戳和级别前缀）
        message = line
        for pattern in self.TIMESTAMP_PATTERNS:
            message = pattern.sub('', message, count=1)
        message = self.LOG_LEVEL_PATTERN.sub('', message, count=1)
        result["message"] = message.strip()

        return result

    def _extract_log_level(self, line: str) -> str:
        """从日志行中提取日志级别

        Args:
            line: 日志行

        Returns:
            日志级别（小写）
        """
        line_upper = line.upper()
        for level in self.LOG_LEVEL_PRIORITY:
            if level.upper() in line_upper:
                return level
        return "info"

    def _normalize_timestamp(self, parsed: dict) -> dict:
        """标准化时间戳

        将各种格式的时间戳替换为统一的短格式。

        Args:
            parsed: 解析后的日志信息

        Returns:
            标准化后的日志信息
        """
        if not parsed["has_timestamp"]:
            return parsed

        original = parsed["original"]
        for pattern in self.TIMESTAMP_PATTERNS:
            match = pattern.search(original)
            if match:
                # 替换为简化时间戳
                original = original[:match.start()] + "[T]" + original[match.end():]
                break

        parsed["original"] = original
        return parsed

    def _deduplicate_patterns(self, parsed_lines: list[dict], ratio: float) -> list[dict]:
        """模式去重

        将相似日志行合并，只保留一条并标注重复次数。

        Args:
            parsed_lines: 解析后的日志行列表
            ratio: 目标压缩率

        Returns:
            去重后的日志行列表
        """
        if ratio > 0.8:
            return parsed_lines

        # 计算消息的相似度分组
        message_groups: dict[str, list[dict]] = {}
        for parsed in parsed_lines:
            if not parsed["original"].strip():
                continue

            # 使用消息的简化版本作为分组键
            key = self._get_pattern_key(parsed["message"])

            if key not in message_groups:
                message_groups[key] = []
            message_groups[key].append(parsed)

        result: list[dict] = []

        for key, group in message_groups.items():
            if len(group) == 1:
                result.append(group[0])
            else:
                # 保留第一条（通常是时间最早的）
                first = group[0]
                count = len(group)

                # 如果重复次数大于阈值，添加重复标记
                if count > 1:
                    first["original"] = first["original"] + f" [x{count}]"

                result.append(first)

        return result

    def _get_pattern_key(self, message: str) -> str:
        """获取消息的模式键

        将消息中的变量部分替换为占位符，用于模式匹配。

        Args:
            message: 日志消息

        Returns:
            模式键
        """
        # 替换数字
        key = re.sub(r'\b\d+[\.\d]*\b', '{N}', message)
        # 替换UUID
        key = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '{UUID}', key, flags=re.IGNORECASE
        )
        # 替换IP地址
        key = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '{IP}', key)
        # 替换文件路径
        key = re.sub(r'[/\\][\w./\\-]+', '{PATH}', key)
        # 替换十六进制字符串
        key = re.sub(r'\b0x[0-9a-fA-F]+\b', '{HEX}', key)

        return key

    def _filter_by_level(self, parsed_lines: list[dict], ratio: float) -> list[str]:
        """按日志级别过滤

        根据压缩率决定保留哪些级别的日志。

        Args:
            parsed_lines: 解析后的日志行列表
            ratio: 目标压缩率

        Returns:
            过滤后的日志行字符串列表
        """
        if ratio > 0.7:
            # 低压缩率：保留所有级别
            return [p["original"] for p in parsed_lines if p["original"].strip()]

        # 根据压缩率确定最低保留级别
        if ratio < 0.3:
            min_priority = 4  # 只保留ERROR及以上
        elif ratio < 0.5:
            min_priority = 3  # 保留WARN及以上
        else:
            min_priority = 2  # 保留INFO及以上

        result: list[str] = []
        for parsed in parsed_lines:
            if not parsed["original"].strip():
                continue

            level = parsed["level"]
            priority = self.LOG_LEVEL_PRIORITY.get(level, 2)

            if priority >= min_priority:
                result.append(parsed["original"])

        # 如果过滤后为空，至少保留ERROR级别
        if not result:
            for parsed in parsed_lines:
                level = parsed["level"]
                if self.LOG_LEVEL_PRIORITY.get(level, 0) >= 4:
                    result.append(parsed["original"])

        return result if result else [p["original"] for p in parsed_lines if p["original"].strip()]
