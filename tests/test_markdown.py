"""
Markdown压缩器测试
"""

import pytest

from tokensqueezer.compressors.markdown import MarkdownCompressor
from tokensqueezer.core.token_counter import TokenCounter


@pytest.fixture
def compressor():
    """创建Markdown压缩器实例"""
    counter = TokenCounter()
    return MarkdownCompressor(counter)


SAMPLE_MARKDOWN = '''# 标题一

## 标题二

这是一些正文内容。

<!-- 这是一个HTML注释，应该被移除 -->

这是一些更多的正文内容。

[这是一个非常长的链接文本，点击这里查看更多详细信息](https://example.com/very/long/path/to/some/resource)

**粗体文本** 和 *斜体文本*

| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 数据1 | 数据2 | 数据3 |
| 数据4 | 数据5 | 数据6 |

![图片描述](https://example.com/image.png)

- 列表项1
- 列表项2
- 列表项3
'''


class TestMarkdownCompressor:
    """Markdown压缩器测试类"""

    def test_html_comment_removal(self, compressor):
        """测试HTML注释移除"""
        result = compressor.compress(SAMPLE_MARKDOWN, ratio=0.5)

        assert result
        assert "<!--" not in result

    def test_heading_preservation(self, compressor):
        """测试标题保留"""
        result = compressor.compress(SAMPLE_MARKDOWN, ratio=0.5)

        assert result
        assert "# 标题一" in result
        assert "## 标题二" in result

    def test_extra_blank_lines_removal(self, compressor):
        """测试多余空行移除"""
        text = "# Title\n\n\n\n\n\nSome content"
        result = compressor.compress(text, ratio=0.5)

        assert result
        assert "\n\n\n" not in result

    def test_link_compression(self, compressor):
        """测试链接压缩"""
        result = compressor.compress(SAMPLE_MARKDOWN, ratio=0.5)

        assert result
        # 长链接文本应被缩短
        assert "这是一个非常长的链接文本，点击这里查看更多详细信息" not in result

    def test_table_optimization(self, compressor):
        """测试表格优化"""
        result = compressor.compress(SAMPLE_MARKDOWN, ratio=0.5)

        assert result
        # 表格应保留
        assert "列1" in result or "数据1" in result

    def test_formatting_simplification(self, compressor):
        """测试格式标记简化"""
        text = "This is **bold** and *italic* text."
        result = compressor.compress(text, ratio=0.3)

        assert result
        # 高压缩率时应移除格式标记
        assert "**bold**" not in result

    def test_image_removal(self, compressor):
        """测试图片移除（高压缩率时）"""
        text = "Some text\n\n![image](https://example.com/img.png)\n\nMore text"
        result = compressor.compress(text, ratio=0.2)

        assert result
        assert "![image]" not in result

    def test_empty_input(self, compressor):
        """测试空输入"""
        assert compressor.compress("", ratio=0.5) == ""
        assert compressor.compress("   ", ratio=0.5) == ""

    def test_list_preservation(self, compressor):
        """测试列表保留"""
        result = compressor.compress(SAMPLE_MARKDOWN, ratio=0.5)

        assert result
        assert "列表项1" in result

    def test_complex_markdown(self, compressor):
        """测试复杂Markdown文档"""
        complex_md = """# Main Title

## Section 1

Some paragraph here with **bold** and *italic* text.

### Subsection

- Item 1
- Item 2
- Item 3

## Section 2

> This is a blockquote

```python
def foo():
    pass
```

[Link text](https://example.com)

| A | B |
|---|---|
| 1 | 2 |
"""
        result = compressor.compress(complex_md, ratio=0.5)

        assert result
        assert "# Main Title" in result
