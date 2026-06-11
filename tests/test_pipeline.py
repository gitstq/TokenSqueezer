"""
压缩管线测试
"""

import pytest

from tokensqueezer.core.compressor import CompressionEngine, CompressionResult
from tokensqueezer.core.content_detector import ContentType
from tokensqueezer.core.pipeline import CompressionPipeline
from tokensqueezer.core.token_counter import TokenCounter


@pytest.fixture
def engine():
    """创建压缩引擎实例"""
    counter = TokenCounter()
    return CompressionEngine(token_counter=counter)


@pytest.fixture
def pipeline():
    """创建压缩管线实例"""
    counter = TokenCounter()
    return CompressionPipeline(token_counter=counter)


class TestCompressionPipeline:
    """压缩管线测试类"""

    def test_single_step_pipeline(self, pipeline):
        """测试单步管线"""
        text = "Hello world. " * 100
        pipeline.add_step(ratio=0.5, name="压缩步骤")

        result = pipeline.run(text)

        assert result
        assert result.compressed_text
        assert result.original_tokens > 0
        assert result.compressor_name == "pipeline"

    def test_multi_step_pipeline(self, pipeline):
        """测试多步管线"""
        text = "Hello world. " * 100
        pipeline.add_step(ratio=0.7, name="轻度压缩")
        pipeline.add_step(ratio=0.5, name="中度压缩")

        result = pipeline.run(text)

        assert result
        assert pipeline.step_count == 2
        assert len(pipeline.results) == 2

    def test_pipeline_summary(self, pipeline):
        """测试管线摘要"""
        text = "Hello world. " * 100
        pipeline.add_step(ratio=0.5, name="压缩")

        pipeline.run(text)
        summary = pipeline.summary()

        assert summary
        assert "压缩管线执行摘要" in summary

    def test_empty_pipeline(self, pipeline):
        """测试空管线（无步骤定义）"""
        text = "Hello world. " * 100

        result = pipeline.run(text)

        assert result
        assert result.compressed_text

    def test_empty_input(self, pipeline):
        """测试空输入"""
        with pytest.raises(ValueError):
            pipeline.run("")

    def test_pipeline_clear(self, pipeline):
        """测试管线清空"""
        pipeline.add_step(ratio=0.5, name="步骤1")
        pipeline.add_step(ratio=0.3, name="步骤2")

        assert pipeline.step_count == 2

        pipeline.clear()

        assert pipeline.step_count == 0
        assert len(pipeline.results) == 0


class TestCompressionEngine:
    """压缩引擎测试类"""

    def test_auto_detection(self, engine):
        """测试自动内容类型检测"""
        text = '{"name": "test", "value": 42}'
        result = engine.compress(text)

        assert result
        assert result.content_type == ContentType.JSON

    def test_explicit_type(self, engine):
        """测试指定内容类型"""
        text = "Some plain text content"
        result = engine.compress(text, content_type=ContentType.TEXT)

        assert result
        assert result.content_type == ContentType.TEXT

    def test_list_compressors(self, engine):
        """测试列出压缩器"""
        compressors = engine.list_compressors()

        assert len(compressors) >= 5
        names = [c["name"] for c in compressors]
        assert "text" in names
        assert "json" in names
        assert "code" in names

    def test_empty_input(self, engine):
        """测试空输入"""
        with pytest.raises(ValueError):
            engine.compress("")

    def test_result_summary(self, engine):
        """测试结果摘要"""
        text = "Hello world. " * 50
        result = engine.compress(text)

        summary = result.summary()
        assert "压缩器:" in summary
        assert "原始Token:" in summary
        assert "节省Token:" in summary

    def test_code_detection(self, engine):
        """测试代码检测"""
        text = "import os\ndef hello():\n    print('hello')\n"
        result = engine.compress(text)

        assert result
        assert result.content_type == ContentType.CODE

    def test_markdown_detection(self, engine):
        """测试Markdown检测"""
        text = "# Title\n\nSome **bold** text\n\n- item 1\n- item 2\n"
        result = engine.compress(text)

        assert result
        assert result.content_type == ContentType.MARKDOWN

    def test_compression_ratio(self, engine):
        """测试压缩率"""
        text = "Hello world. " * 200
        result = engine.compress(text, ratio=0.5)

        assert result
        assert result.ratio <= 1.0
        assert result.saved_tokens >= 0
