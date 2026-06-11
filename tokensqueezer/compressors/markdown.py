"""
Markdown压缩器

实现Markdown文档的智能压缩，保留标题结构，
移除多余格式，优化链接和表格。
"""

import re
from typing import Optional

from tokensqueezer.core.compressor import CompressorBase
from tokensqueezer.core.content_detector import ContentType
from tokensqueezer.core.token_counter import TokenCounter


class MarkdownCompressor(CompressorBase):
    """Markdown压缩器

    通过移除多余空行、压缩链接、优化表格和保留标题结构来压缩Markdown。

    压缩率目标：30-50%
    """

    name: str = "markdown"
    supported_types: list = [ContentType.MARKDOWN]
    description: str = "Markdown压缩器 - 保留结构、优化格式"

    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """初始化Markdown压缩器"""
        super().__init__(token_counter)

    def compress(self, text: str, ratio: float = 0.5) -> str:
        """压缩Markdown文本

        执行以下压缩步骤：
        1. 移除多余空行
        2. 压缩链接
        3. 优化表格
        4. 简化格式标记
        5. 移除HTML注释

        Args:
            text: Markdown文本
            ratio: 目标压缩率（0.1-0.9）

        Returns:
            压缩后的Markdown
        """
        if not text or not text.strip():
            return ""

        ratio = self.validate_ratio(ratio)
        result = text

        # 步骤1：移除HTML注释
        result = self._remove_html_comments(result)

        # 步骤2：移除多余空行
        result = self._remove_extra_blank_lines(result)

        # 步骤3：压缩链接
        if ratio < 0.7:
            result = self._compress_links(result)

        # 步骤4：优化表格
        result = self._optimize_tables(result)

        # 步骤5：简化格式标记
        if ratio < 0.5:
            result = self._simplify_formatting(result)

        # 步骤6：移除图片（高压缩率时）
        if ratio < 0.3:
            result = self._remove_images(result)

        # 确保结果非空
        if not result.strip():
            return text.strip()

        return result.strip()

    def _remove_html_comments(self, text: str) -> str:
        """移除HTML注释

        Args:
            text: Markdown文本

        Returns:
            移除注释后的文本
        """
        return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    def _remove_extra_blank_lines(self, text: str) -> str:
        """移除多余的空行

        保留标题前后的空行，移除其他多余空行。

        Args:
            text: Markdown文本

        Returns:
            压缩后的文本
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

    def _compress_links(self, text: str) -> str:
        """压缩Markdown链接

        将 [文本](URL) 格式简化为仅保留URL或缩短文本。

        Args:
            text: Markdown文本

        Returns:
            压缩后的文本
        """
        # 压缩完整链接为仅URL
        def replace_link(match: re.Match) -> str:
            link_text = match.group(1)
            url = match.group(2)

            # 如果链接文本很长，缩短它
            if len(link_text) > 20:
                # 取前10个字符
                short_text = link_text[:10].strip()
                if len(link_text) > 10:
                    short_text += "..."
                return f"[{short_text}]({url})"

            return match.group(0)

        # 匹配Markdown链接 [text](url)
        result = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replace_link, text)

        return result

    def _optimize_tables(self, text: str) -> str:
        """优化Markdown表格

        移除表格中的多余空格和对齐分隔行。

        Args:
            text: Markdown文本

        Returns:
            优化后的文本
        """
        lines = text.split('\n')
        result: list[str] = []
        in_table = False

        for line in lines:
            stripped = line.strip()

            # 检测表格分隔行
            if re.match(r'^\|?[\s\-:|]+\|?$', stripped):
                # 简化分隔行
                if in_table:
                    result.append('|---|')
                continue

            # 检测表格行
            if '|' in stripped and stripped.startswith('|'):
                in_table = True
                # 移除单元格内多余空格
                cells = [c.strip() for c in stripped.split('|')]
                result.append('|'.join(cells))
            elif stripped.startswith('|') and stripped.endswith('|'):
                in_table = True
                cells = [c.strip() for c in stripped.split('|')]
                result.append('|'.join(cells))
            else:
                in_table = False
                result.append(line)

        return '\n'.join(result)

    def _simplify_formatting(self, text: str) -> str:
        """简化格式标记

        移除不必要的粗体/斜体标记（保留标题中的标记）。

        Args:
            text: Markdown文本

        Returns:
            简化后的文本
        """
        lines = text.split('\n')
        result: list[str] = []

        for line in lines:
            # 跳过标题行
            if line.strip().startswith('#'):
                result.append(line)
                continue

            # 移除粗体标记（保留内容）
            line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
            # 移除斜体标记（保留内容）
            line = re.sub(r'\*([^*]+)\*', r'\1', line)
            # 移除删除线标记
            line = re.sub(r'~~([^~]+)~~', r'\1', line)

            result.append(line)

        return '\n'.join(result)

    def _remove_images(self, text: str) -> str:
        """移除Markdown图片

        将图片标记替换为简短的占位符。

        Args:
            text: Markdown文本

        Returns:
            移除图片后的文本
        """
        return re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', '[图片]', text)
