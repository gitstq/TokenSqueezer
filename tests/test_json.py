"""
JSON压缩器测试
"""

import json

import pytest

from tokensqueezer.compressors.json import JsonCompressor
from tokensqueezer.core.token_counter import TokenCounter


@pytest.fixture
def compressor():
    """创建JSON压缩器实例"""
    counter = TokenCounter()
    return JsonCompressor(counter)


class TestJsonCompressor:
    """JSON压缩器测试类"""

    def test_basic_json_compression(self, compressor):
        """测试基本JSON压缩

        验证压缩器能正确处理JSON输入并输出有效JSON。
        """
        data = {
            "name": "test",
            "value": 42,
            "items": [1, 2, 3, 4, 5],
        }
        text = json.dumps(data)
        result = compressor.compress(text, ratio=0.5)

        assert result
        # 结果应为有效JSON
        parsed = json.loads(result)
        assert "name" in parsed

    def test_array_deduplication(self, compressor):
        """测试数组去重"""
        data = {
            "items": [1, 2, 3, 1, 2, 3, 4, 5],
        }
        text = json.dumps(data)
        result = compressor.compress(text, ratio=0.5)

        assert result
        parsed = json.loads(result)
        # 重复元素应被移除
        assert len(parsed["items"]) <= 6

    def test_field_pruning(self, compressor):
        """测试字段裁剪"""
        data = {
            "id": 1,
            "name": "test",
            "timestamp": "2024-01-01T00:00:00",
            "metadata": {"key": "value"},
            "trace_id": "abc123",
        }
        text = json.dumps(data)
        result = compressor.compress(text, ratio=0.3)

        assert result
        parsed = json.loads(result)
        # 高压缩率时应移除低信息量字段
        assert "id" in parsed  # 高优先级字段应保留

    def test_string_truncation(self, compressor):
        """测试字符串值截断"""
        data = {
            "short_text": "hello",
            "long_text": "a" * 1000,
        }
        text = json.dumps(data)
        result = compressor.compress(text, ratio=0.3)

        assert result
        parsed = json.loads(result)
        # 长字符串应被截断
        assert len(parsed.get("long_text", "")) < 1000

    def test_empty_input(self, compressor):
        """测试空输入"""
        assert compressor.compress("", ratio=0.5) == ""
        assert compressor.compress("   ", ratio=0.5) == ""

    def test_invalid_json(self, compressor):
        """测试无效JSON输入"""
        text = "this is not json"
        result = compressor.compress(text, ratio=0.5)

        # 无效JSON应返回原始文本
        assert result == text

    def test_nested_structure(self, compressor):
        """测试嵌套结构压缩"""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep nested value"
                    }
                }
            }
        }
        text = json.dumps(data)
        result = compressor.compress(text, ratio=0.5)

        assert result
        parsed = json.loads(result)
        assert "level1" in parsed

    def test_large_array(self, compressor):
        """测试大数组压缩"""
        data = {
            "items": list(range(100)),
        }
        text = json.dumps(data)
        result = compressor.compress(text, ratio=0.3)

        assert result
        parsed = json.loads(result)
        # 大数组应被截断
        assert len(parsed["items"]) < 100
