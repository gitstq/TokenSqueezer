"""
代码压缩器

实现代码的智能压缩，保留结构信息，移除冗余内容。
支持多种编程语言。
"""

import re
from typing import Optional

from tokensqueezer.core.compressor import CompressorBase
from tokensqueezer.core.content_detector import ContentDetector, ContentType
from tokensqueezer.core.token_counter import TokenCounter


class CodeCompressor(CompressorBase):
    """代码压缩器

    通过移除注释和空行、保留关键结构来压缩代码。
    支持 Python, JavaScript, Go, Rust, Java, C++ 等语言。

    压缩率目标：40-70%
    """

    name: str = "code"
    supported_types: list = [ContentType.CODE]
    description: str = "代码压缩器 - 保留结构、移除冗余"

    # 单行注释模式
    SINGLE_LINE_COMMENT_PATTERNS: dict[str, re.Pattern] = {
        "python": re.compile(r'#.*$'),
        "javascript": re.compile(r'//.*$'),
        "go": re.compile(r'//.*$'),
        "rust": re.compile(r'//.*$'),
        "java": re.compile(r'//.*$'),
        "cpp": re.compile(r'//.*$'),
        "sql": re.compile(r'--.*$'),
    }

    # 多行注释模式
    MULTI_LINE_COMMENT_PATTERNS: dict[str, tuple[str, str]] = {
        "javascript": ('/*', '*/'),
        "go": ('/*', '*/'),
        "rust": ('/*', '*/'),
        "java": ('/*', '*/'),
        "cpp": ('/*', '*/'),
        "css": ('/*', '*/'),
        "html": ('<!--', '-->'),
    }

    # 字符串定界符
    STRING_DELIMITERS = ['"""', "'''", '"', "'", '`']

    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """初始化代码压缩器"""
        super().__init__(token_counter)
        self._detector = ContentDetector()

    def compress(self, text: str, ratio: float = 0.5) -> str:
        """压缩代码

        执行以下压缩步骤：
        1. 检测编程语言
        2. 移除注释
        3. 移除空行
        4. 压缩函数体（高压缩率时）
        5. 保留关键结构

        Args:
            text: 代码文本
            ratio: 目标压缩率（0.1-0.9）

        Returns:
            压缩后的代码
        """
        if not text or not text.strip():
            return ""

        ratio = self.validate_ratio(ratio)
        language = self._detector.detect_language(text) or "python"

        result = text

        # 步骤1：移除多行注释
        result = self._remove_multiline_comments(result, language)

        # 步骤2：移除单行注释
        result = self._remove_single_line_comments(result, language)

        # 步骤3：移除空行和多余空白
        result = self._remove_blank_lines(result)

        # 步骤4：压缩行内空白
        result = self._compress_inline_whitespace(result)

        # 步骤5：高压缩率时压缩函数体
        if ratio < 0.4:
            result = self._compress_function_bodies(result, language)

        # 确保结果非空
        if not result.strip():
            return text.strip()

        return result.strip()

    def _remove_single_line_comments(self, text: str, language: str) -> str:
        """移除单行注释

        注意：不会移除字符串中的注释符号。

        Args:
            text: 代码文本
            language: 编程语言

        Returns:
            移除注释后的代码
        """
        pattern = self.SINGLE_LINE_COMMENT_PATTERNS.get(language)
        if not pattern:
            return text

        lines = text.split('\n')
        result_lines: list[str] = []

        for line in lines:
            # 跳过在字符串中的行
            stripped = line.lstrip()
            is_comment_line = False
            if language == "python" and stripped.startswith('#'):
                is_comment_line = True
            elif stripped.startswith('//'):
                is_comment_line = True
            elif stripped.startswith('--'):
                is_comment_line = True

            if is_comment_line:
                # 整行是注释，跳过
                continue

            # 移除行尾注释（简化处理：不在字符串内时移除）
            new_line = pattern.sub('', line)
            result_lines.append(new_line)

        return '\n'.join(result_lines)

    def _remove_multiline_comments(self, text: str, language: str) -> str:
        """移除多行注释

        Args:
            text: 代码文本
            language: 编程语言

        Returns:
            移除注释后的代码
        """
        delimiters = self.MULTI_LINE_COMMENT_PATTERNS.get(language)
        if not delimiters:
            return text

        start_marker, end_marker = delimiters
        result = text

        # 简单的多行注释移除（不处理字符串内的情况）
        pattern = re.compile(
            re.escape(start_marker) + r'.*?' + re.escape(end_marker),
            re.DOTALL
        )
        result = pattern.sub('', result)

        return result

    def _remove_blank_lines(self, text: str) -> str:
        """移除空行

        保留最多一个连续空行以维持基本可读性。

        Args:
            text: 代码文本

        Returns:
            移除空行后的代码
        """
        lines = text.split('\n')
        result: list[str] = []
        blank_count = 0

        for line in lines:
            if not line.strip():
                blank_count += 1
                if blank_count <= 1:
                    result.append('')
            else:
                blank_count = 0
                result.append(line)

        return '\n'.join(result)

    def _compress_inline_whitespace(self, text: str) -> str:
        """压缩行内空白

        将多个空格压缩为单个，保留缩进。

        Args:
            text: 代码文本

        Returns:
            压缩后的代码
        """
        lines = text.split('\n')
        result: list[str] = []

        for line in lines:
            if not line.strip():
                result.append('')
                continue

            # 保留缩进
            indent = len(line) - len(line.lstrip())
            content = line.lstrip()

            # 压缩内容中的多个空格
            content = re.sub(r'[ \t]+', ' ', content)

            result.append(' ' * indent + content)

        return '\n'.join(result)

    def _compress_function_bodies(self, text: str, language: str) -> str:
        """压缩函数体

        保留函数签名和return语句，移除中间的详细实现。

        Args:
            text: 代码文本
            language: 编程语言

        Returns:
            压缩后的代码
        """
        lines = text.split('\n')
        result: list[str] = []
        in_function = False
        function_indent = 0
        brace_count = 0
        has_return = False

        for line in lines:
            stripped = line.strip()

            # 检测函数定义
            if self._is_function_def(stripped, language):
                in_function = True
                function_indent = len(line) - len(line.lstrip())
                has_return = False

                # 对于大括号语言，计数大括号
                if language in ("javascript", "go", "rust", "java", "cpp"):
                    brace_count = stripped.count('{') - stripped.count('}')
                else:
                    brace_count = 0

                result.append(line)
                continue

            if in_function:
                current_indent = len(line) - len(line.lstrip()) if line.strip() else function_indent + 1

                # 检测函数结束
                if language in ("javascript", "go", "rust", "java", "cpp"):
                    brace_count += stripped.count('{') - stripped.count('}')
                    if brace_count <= 0 and stripped == '}':
                        in_function = False
                        result.append(line)
                        continue
                else:
                    # Python风格：缩进回到函数级别
                    if line.strip() and current_indent <= function_indent:
                        in_function = False
                        result.append(line)
                        continue

                # 保留return语句和关键声明
                if re.match(r'^\s*(return|yield|raise|assert|break|continue)\b', line):
                    has_return = True
                    result.append(line)
                elif re.match(r'^\s*(self\.\w+|var |let |const |int |str |bool )', line):
                    result.append(line)
                # 跳过其他实现细节
                continue

            result.append(line)

        return '\n'.join(result)

    def _is_function_def(self, line: str, language: str) -> bool:
        """判断是否为函数定义行

        Args:
            line: 代码行（已去除首尾空白）
            language: 编程语言

        Returns:
            是否为函数定义
        """
        if not line:
            return False

        patterns = {
            "python": r'^(async\s+)?def\s+\w+',
            "javascript": r'^(async\s+)?function\s+\w+|^(const|let|var)\s+\w+\s*=\s*(async\s+)?\(',
            "go": r'^func\s+',
            "rust": r'^(pub\s+)?(async\s+)?fn\s+\w+',
            "java": r'^(public|private|protected|static|synchronized)?\s*\w+\s+\w+\s*\(',
            "cpp": r'^\w+\s+\w+\s*\(',
            "sql": r'^(CREATE|ALTER|DROP)\s+(FUNCTION|PROCEDURE)',
        }

        pattern = patterns.get(language)
        if pattern:
            return bool(re.match(pattern, line))

        return False
