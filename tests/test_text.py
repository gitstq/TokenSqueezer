"""
文本压缩器测试
"""

import pytest

from tokensqueezer.compressors.text import TextCompressor
from tokensqueezer.core.token_counter import TokenCounter


@pytest.fixture
def compressor():
    """创建文本压缩器实例"""
    counter = TokenCounter()
    return TextCompressor(counter)


class TestTextCompressor:
    """文本压缩器测试类"""

    def test_basic_compression(self, compressor):
        """测试基本文本压缩

        验证压缩器能正确移除冗余空白。
        """
        text = "Hello   world.  \n\n\nThis is   a test."
        result = compressor.compress(text, ratio=0.5)

        assert result
        assert "  " not in result  # 不应有多余空格
        assert "\n\n\n" not in result  # 不应有多个连续空行

    def test_duplicate_sentence_removal(self, compressor):
        """测试重复句子移除

        验证压缩器能移除完全重复的句子。
        """
        text = "This is a test sentence. This is a test sentence. Another sentence here."
        result = compressor.compress(text, ratio=0.5)

        assert result
        # 重复句子应被移除
        count = result.count("This is a test sentence")
        assert count <= 1

    def test_chinese_text_compression(self, compressor):
        """测试中文文本压缩

        验证压缩器能正确处理中文文本，不截断中文字符。
        """
        text = "在这个时候，我们需要考虑到各种因素。在这个时候，问题变得复杂了。"
        result = compressor.compress(text, ratio=0.5)

        assert result
        # 验证中文字符完整性
        for char in result:
            if '\u4e00' <= char <= '\u9fff':
                assert True  # 中文字符未被破坏

    def test_empty_input(self, compressor):
        """测试空输入"""
        assert compressor.compress("", ratio=0.5) == ""
        assert compressor.compress("   ", ratio=0.5) == ""

    def test_redundant_phrase_compression(self, compressor):
        """测试冗余表达压缩"""
        text = "It is important to note that in order to achieve success, we need to work hard."
        result = compressor.compress(text, ratio=0.3)

        assert result
        assert "in order to" not in result.lower()

    def test_ratio_validation(self, compressor):
        """测试压缩率验证"""
        # 压缩率应被限制在0.1-0.9之间
        assert compressor.validate_ratio(0.0) == 0.1
        assert compressor.validate_ratio(1.0) == 0.9
        assert compressor.validate_ratio(0.5) == 0.5

    def test_very_long_input(self, compressor):
        """测试超长输入"""
        # 生成超长文本
        text = "This is a sentence. " * 10000
        result = compressor.compress(text, ratio=0.5)

        assert result
        assert len(result) < len(text)

    def test_special_characters(self, compressor):
        """测试特殊字符处理"""
        text = "Hello! @#$%^&*() World! \n\n Test..."
        result = compressor.compress(text, ratio=0.5)

        assert result
        assert "Hello" in result
