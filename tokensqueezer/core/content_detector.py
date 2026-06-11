"""
内容类型检测器

自动检测输入内容的类型，支持基于文件扩展名和内容特征的混合检测。
"""

import json
import re
from enum import Enum
from typing import Optional


class ContentType(Enum):
    """内容类型枚举"""
    TEXT = "text"
    JSON = "json"
    CODE = "code"
    MARKDOWN = "markdown"
    LOG = "log"


class ContentDetector:
    """内容类型检测器

    通过文件扩展名和内容特征自动检测输入内容的类型。
    支持代码语言识别（Python, JavaScript, Go, Rust, Java, C++等）。
    """

    # 文件扩展名到内容类型的映射
    EXTENSION_MAP: dict[str, ContentType] = {
        # JSON
        ".json": ContentType.JSON,
        # 代码
        ".py": ContentType.CODE,
        ".js": ContentType.CODE,
        ".ts": ContentType.CODE,
        ".tsx": ContentType.CODE,
        ".jsx": ContentType.CODE,
        ".go": ContentType.CODE,
        ".rs": ContentType.CODE,
        ".java": ContentType.CODE,
        ".c": ContentType.CODE,
        ".cpp": ContentType.CODE,
        ".cc": ContentType.CODE,
        ".h": ContentType.CODE,
        ".hpp": ContentType.CODE,
        ".cs": ContentType.CODE,
        ".rb": ContentType.CODE,
        ".php": ContentType.CODE,
        ".swift": ContentType.CODE,
        ".kt": ContentType.CODE,
        ".scala": ContentType.CODE,
        ".r": ContentType.CODE,
        ".R": ContentType.CODE,
        ".lua": ContentType.CODE,
        ".sh": ContentType.CODE,
        ".bash": ContentType.CODE,
        ".zsh": ContentType.CODE,
        ".ps1": ContentType.CODE,
        ".sql": ContentType.CODE,
        ".html": ContentType.CODE,
        ".css": ContentType.CODE,
        ".scss": ContentType.CODE,
        ".less": ContentType.CODE,
        ".xml": ContentType.CODE,
        ".yaml": ContentType.CODE,
        ".yml": ContentType.CODE,
        ".toml": ContentType.CODE,
        ".ini": ContentType.CODE,
        ".cfg": ContentType.CODE,
        ".dockerfile": ContentType.CODE,
        # Markdown
        ".md": ContentType.MARKDOWN,
        ".mdx": ContentType.MARKDOWN,
        ".rst": ContentType.MARKDOWN,
        # 日志
        ".log": ContentType.LOG,
    }

    # 代码语言关键字模式
    CODE_PATTERNS: dict[str, re.Pattern] = {
        "python": re.compile(
            r'^\s*(import |from \w+ import |def \w+|class \w+|if __name__|'
            r'@\w+|print\(|self\.)',
            re.MULTILINE
        ),
        "javascript": re.compile(
            r'^\s*(const |let |var |function |=> |console\.|require\(|'
            r'export |import |module\.exports)',
            re.MULTILINE
        ),
        "go": re.compile(
            r'^\s*(package |import \(|func |type |struct |interface |'
            r'fmt\.|go |chan |goroutine)',
            re.MULTILINE
        ),
        "rust": re.compile(
            r'^\s*(use |fn |let |mut |impl |pub |struct |enum |'
            r'mod |match |println!|vec!|String::)',
            re.MULTILINE
        ),
        "java": re.compile(
            r'^\s*(import |public |private |protected |class |interface |'
            r'static |void |System\.out|package )',
            re.MULTILINE
        ),
        "cpp": re.compile(
            r'^\s*(#include |using namespace|std::|int main|class |'
            r'template |namespace |virtual |override)',
            re.MULTILINE
        ),
        "sql": re.compile(
            r'^\s*(SELECT |INSERT |UPDATE |DELETE |CREATE |ALTER |DROP |'
            r'FROM |WHERE |JOIN |GROUP BY|ORDER BY)',
            re.MULTILINE | re.IGNORECASE
        ),
    }

    # 日志模式
    LOG_PATTERNS: list[re.Pattern] = [
        re.compile(r'^\d{4}[-/]\d{2}[-/]\d{2}[\sT]'),       # 日期开头
        re.compile(r'^\[\d{4}-\d{2}-\d{2}'),                  # [日期] 格式
        re.compile(r'^\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}'),  # syslog格式
        re.compile(r'^\d{2}:\d{2}:\d{2}'),                     # 时间开头
        re.compile(r'(ERROR|WARN|INFO|DEBUG|TRACE)\s*[-=:]', re.IGNORECASE),  # 日志级别
        re.compile(r'\[ERROR\]|\[WARN\]|\[INFO\]|\[DEBUG\]', re.IGNORECASE),  # [级别] 格式
        re.compile(r'level=(error|warn|info|debug)', re.IGNORECASE),           # level= 格式
    ]

    # Markdown模式
    MARKDOWN_PATTERNS: list[re.Pattern] = [
        re.compile(r'^#{1,6}\s+\S', re.MULTILINE),       # 标题
        re.compile(r'\[.+\]\(.+\)'),                       # 链接
        re.compile(r'!\[.*\]\(.+\)'),                      # 图片
        re.compile(r'^\s*[-*+]\s+\S', re.MULTILINE),     # 无序列表
        re.compile(r'^\s*\d+\.\s+\S', re.MULTILINE),      # 有序列表
        re.compile(r'^\s*>\s+\S', re.MULTILINE),          # 引用
        re.compile(r'\*\*[^*]+\*\*'),                      # 粗体
        re.compile(r'```[\w]*\n'),                          # 代码块
    ]

    def detect(self, text: str, filename: Optional[str] = None) -> ContentType:
        """检测内容类型

        优先使用文件扩展名检测，如果无法确定则使用内容特征检测。

        Args:
            text: 输入文本
            filename: 可选的文件名（用于扩展名检测）

        Returns:
            检测到的内容类型
        """
        if not text or not text.strip():
            return ContentType.TEXT

        # 优先通过文件扩展名检测
        if filename:
            ext = self._get_extension(filename)
            if ext and ext.lower() in self.EXTENSION_MAP:
                return self.EXTENSION_MAP[ext.lower()]

        # 通过内容特征检测
        return self._detect_by_content(text)

    def detect_language(self, text: str) -> Optional[str]:
        """检测代码语言

        Args:
            text: 输入文本

        Returns:
            语言名称（如 "python", "javascript"），如果不是代码则返回None
        """
        for language, pattern in self.CODE_PATTERNS.items():
            if pattern.search(text):
                return language
        return None

    def _detect_by_content(self, text: str) -> ContentType:
        """通过内容特征检测类型

        按优先级依次检测：JSON > Markdown > 日志 > 代码 > 文本

        Args:
            text: 输入文本

        Returns:
            检测到的内容类型
        """
        # 检测JSON
        if self._is_json(text):
            return ContentType.JSON

        # 检测Markdown（需要至少2个Markdown特征）
        md_score = sum(1 for p in self.MARKDOWN_PATTERNS if p.search(text))
        if md_score >= 2:
            return ContentType.MARKDOWN

        # 检测日志（需要至少2个日志特征或高密度日志行）
        if self._is_log(text):
            return ContentType.LOG

        # 检测代码
        if self.detect_language(text) is not None:
            return ContentType.CODE

        # 默认为文本
        return ContentType.TEXT

    def _is_json(self, text: str) -> bool:
        """判断文本是否为JSON格式

        Args:
            text: 输入文本

        Returns:
            是否为有效JSON
        """
        stripped = text.strip()
        if not (stripped.startswith('{') or stripped.startswith('[')):
            return False
        try:
            json.loads(stripped)
            return True
        except (json.JSONDecodeError, ValueError):
            return False

    def _is_log(self, text: str) -> bool:
        """判断文本是否为日志格式

        Args:
            text: 输入文本

        Returns:
            是否为日志格式
        """
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return False

        # 统计匹配日志模式的行数
        log_line_count = 0
        for line in lines[:20]:  # 只检查前20行
            for pattern in self.LOG_PATTERNS:
                if pattern.search(line):
                    log_line_count += 1
                    break

        # 如果超过50%的行匹配日志模式，则认为是日志
        return log_line_count / min(len(lines), 20) >= 0.5

    def _get_extension(self, filename: str) -> Optional[str]:
        """从文件名中提取扩展名

        Args:
            filename: 文件名

        Returns:
            文件扩展名（包含点号），如果没有则返回None
        """
        if '.' not in filename:
            return None
        # 处理 .dockerfile 等特殊情况
        parts = filename.rsplit('.', 1)
        if len(parts) == 2:
            return '.' + parts[1].lower()
        return None
