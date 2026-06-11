"""
Token计数器

基于tiktoken的精确Token计数，支持多种编码格式。
"""

import functools
from typing import Optional


class TokenCounter:
    """Token计数器

    使用tiktoken进行精确的Token计数，支持多种编码格式。
    对于无法使用tiktoken的情况，提供基于字符的估算回退方案。
    """

    # 支持的编码名称
    SUPPORTED_ENCODINGS = {
        "cl100k_base": "cl100k_base",       # GPT-4, GPT-3.5-turbo
        "p50k_base": "p50k_base",           # text-davinci-003
        "p50k_edit": "p50k_edit",            # 代码编辑模型
        "r50k_base": "r50k_base",            # 旧版模型
    }

    # 默认编码
    DEFAULT_ENCODING = "cl100k_base"

    def __init__(self, encoding_name: str = DEFAULT_ENCODING):
        """初始化Token计数器

        Args:
            encoding_name: tiktoken编码名称，默认为cl100k_base

        Raises:
            ValueError: 当编码名称不支持时
        """
        if encoding_name not in self.SUPPORTED_ENCODINGS:
            raise ValueError(
                f"不支持的编码: {encoding_name}。"
                f"支持的编码: {list(self.SUPPORTED_ENCODINGS.keys())}"
            )

        self._encoding_name = encoding_name
        self._encoding = None
        self._tiktoken_available = True
        self._load_encoding()

    def _load_encoding(self) -> None:
        """加载tiktoken编码器"""
        try:
            import tiktoken
            self._encoding = tiktoken.get_encoding(self._encoding_name)
        except (ImportError, Exception):
            self._tiktoken_available = False

    def count(self, text: str) -> int:
        """计算文本的Token数量

        如果tiktoken可用，使用精确计数。
        否则使用基于字符的估算（中文约1.5字符/token，英文约4字符/token）。

        Args:
            text: 输入文本

        Returns:
            Token数量
        """
        if not text:
            return 0

        if self._tiktoken_available and self._encoding is not None:
            try:
                tokens = self._encoding.encode(text)
                return len(tokens)
            except Exception:
                # tiktoken调用失败，回退到估算
                pass

        return self._estimate_tokens(text)

    def count_batch(self, texts: list[str]) -> list[int]:
        """批量计算Token数量

        Args:
            texts: 文本列表

        Returns:
            Token数量列表，与输入顺序对应
        """
        return [self.count(text) for text in texts]

    def _estimate_tokens(self, text: str) -> int:
        """估算Token数量（回退方案）

        基于字符数估算：
        - 中文字符：约1.5字符/token
        - 英文和其他字符：约4字符/token

        Args:
            text: 输入文本

        Returns:
            估算的Token数量
        """
        if not text:
            return 0

        chinese_chars = 0
        other_chars = 0

        for char in text:
            # 判断是否为中文字符（CJK统一表意文字）
            if '\u4e00' <= char <= '\u9fff':
                chinese_chars += 1
            else:
                other_chars += 1

        # 中文约1.5字符/token，英文约4字符/token
        estimated = int(chinese_chars / 1.5 + other_chars / 4.0)
        return max(1, estimated)

    @property
    def encoding_name(self) -> str:
        """当前使用的编码名称"""
        return self._encoding_name

    @property
    def is_tiktoken_available(self) -> bool:
        """tiktoken是否可用"""
        return self._tiktoken_available

    def __repr__(self) -> str:
        status = "tiktoken" if self._tiktoken_available else "estimate"
        return f"<TokenCounter(encoding={self._encoding_name}, mode={status})>"
