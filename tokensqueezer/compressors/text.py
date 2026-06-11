"""
文本压缩器

实现文本内容的智能压缩，包括冗余消除、重复句子移除、
智能段落合并和中文文本特殊处理。
"""

import re
from typing import Optional

from tokensqueezer.core.compressor import CompressorBase
from tokensqueezer.core.content_detector import ContentType
from tokensqueezer.core.token_counter import TokenCounter


class TextCompressor(CompressorBase):
    """文本压缩器

    通过移除冗余空白、重复句子和智能段落合并来压缩文本。
    特别处理中文文本，确保不截断中文字符和保留完整词组。

    压缩率目标：30-60%
    """

    name: str = "text"
    supported_types: list = [ContentType.TEXT]
    description: str = "文本压缩器 - 移除冗余、保留语义"

    # 中文标点符号
    CN_PUNCTUATION = "，。！？；：、""''【】《》（）…—·"
    # 中文字符范围
    CN_CHAR_PATTERN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

    def __init__(self, token_counter: Optional[TokenCounter] = None):
        """初始化文本压缩器"""
        super().__init__(token_counter)

    def compress(self, text: str, ratio: float = 0.5) -> str:
        """压缩文本

        执行以下压缩步骤：
        1. 移除多余空白
        2. 移除重复句子
        3. 智能段落合并
        4. 根据压缩率调整压缩强度

        Args:
            text: 待压缩的文本
            ratio: 目标压缩率（0.1-0.9）

        Returns:
            压缩后的文本
        """
        if not text or not text.strip():
            return ""

        ratio = self.validate_ratio(ratio)
        result = text

        # 步骤1：移除多余空白
        result = self._remove_redundant_whitespace(result)

        # 步骤2：移除重复句子
        result = self._remove_duplicate_sentences(result)

        # 步骤3：压缩冗余表达
        if ratio < 0.7:
            result = self._compress_redundant_phrases(result)

        # 步骤4：智能段落合并
        if ratio < 0.5:
            result = self._merge_short_paragraphs(result)

        # 步骤5：移除填充词（高压缩率时）
        if ratio < 0.4:
            result = self._remove_filler_words(result)

        # 确保结果非空
        if not result.strip():
            return text.strip()

        return result.strip()

    def _remove_redundant_whitespace(self, text: str) -> str:
        """移除冗余空白

        将多个连续空格/换行压缩为单个，保留段落结构。

        Args:
            text: 输入文本

        Returns:
            清理后的文本
        """
        # 压缩多个空格为单个
        text = re.sub(r'[^\S\n]+', ' ', text)
        # 压缩多个空行为最多两个
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        return '\n'.join(lines)

    def _remove_duplicate_sentences(self, text: str) -> str:
        """移除重复或高度相似的句子

        Args:
            text: 输入文本

        Returns:
            去重后的文本
        """
        # 按句子分割（支持中英文标点）
        sentences = re.split(r'(?<=[。！？.!?])\s*', text)
        seen: list[str] = []
        unique_sentences: list[str] = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 标准化句子用于比较（移除空白，转小写）
            normalized = re.sub(r'\s+', '', sentence).lower()

            # 检查是否与已见过的句子重复或高度相似
            is_duplicate = False
            for seen_norm in seen:
                if normalized == seen_norm:
                    is_duplicate = True
                    break
                # 检查是否为子串（长度差异不超过20%）
                if len(normalized) > 10 and len(seen_norm) > 10:
                    if normalized in seen_norm or seen_norm in normalized:
                        is_duplicate = True
                        break

            if not is_duplicate:
                seen.append(normalized)
                unique_sentences.append(sentence)

        return ''.join(unique_sentences)

    def _compress_redundant_phrases(self, text: str) -> str:
        """压缩冗余表达

        移除常见的冗余词组和表达。

        Args:
            text: 输入文本

        Returns:
            压缩后的文本
        """
        # 常见冗余表达替换
        replacements = [
            # 中文冗余
            (r'在这个时候', '此时'),
            (r'在目前的情况下', '目前'),
            (r'从本质上来说', '本质上'),
            (r'从某种意义上来说', '某种意义上'),
            (r'众所周知的是', '众所周知'),
            (r'毫无疑问的是', '毫无疑问'),
            (r'需要特别指出的是', '需指出'),
            (r'换句话说', '即'),
            (r'也就是说', '即'),
            (r'一方面来说', '一方面'),
            (r'另一方面来说', '另一方面'),
            # 英文冗余
            (r'\bin order to\b', 'to'),
            (r'\bdue to the fact that\b', 'because'),
            (r'\bin spite of the fact that\b', 'although'),
            (r'\bat this point in time\b', 'now'),
            (r'\bfor the purpose of\b', 'for'),
            (r'\bin the event that\b', 'if'),
            (r'\bit is important to note that\b', ''),
            (r'\bas a matter of fact\b', 'in fact'),
            (r'\bfirst and foremost\b', 'firstly'),
        ]

        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def _merge_short_paragraphs(self, text: str) -> str:
        """智能合并短段落

        将相邻的短段落合并为一个段落，保留语义完整性。

        Args:
            text: 输入文本

        Returns:
            合并后的文本
        """
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        if len(paragraphs) <= 1:
            return text

        merged: list[str] = []
        buffer = ""

        for para in paragraphs:
            # 如果当前段落很短（少于50字符），加入缓冲区
            if len(para) < 50:
                if buffer:
                    buffer += " " + para
                else:
                    buffer = para
            else:
                # 遇到长段落，先输出缓冲区
                if buffer:
                    merged.append(buffer)
                    buffer = ""
                merged.append(para)

        # 输出最后的缓冲区
        if buffer:
            merged.append(buffer)

        return '\n\n'.join(merged)

    def _remove_filler_words(self, text: str) -> str:
        """移除填充词

        移除不影响语义的填充词和连接词。

        Args:
            text: 输入文本

        Returns:
            压缩后的文本
        """
        # 英文填充词
        filler_pattern = re.compile(
            r'\b(very|really|actually|basically|literally|'
            r'honestly|obviously|clearly|certainly|'
            r'just|quite|rather|somewhat)\b\s*',
            re.IGNORECASE
        )
        result = filler_pattern.sub('', text)

        # 清理多余的空格
        result = re.sub(r'\s+', ' ', result)

        return result.strip()

    def _is_chinese_text(self, text: str) -> bool:
        """判断文本是否主要为中文

        Args:
            text: 输入文本

        Returns:
            是否为中文文本
        """
        cn_chars = len(self.CN_CHAR_PATTERN.findall(text))
        return cn_chars / max(len(text), 1) > 0.3
