"""
日志压缩器测试
"""

import pytest

from tokensqueezer.compressors.log import LogCompressor
from tokensqueezer.core.token_counter import TokenCounter


@pytest.fixture
def compressor():
    """创建日志压缩器实例"""
    counter = TokenCounter()
    return LogCompressor(counter)


SAMPLE_LOGS = """2024-01-15 10:30:01 INFO  Application started successfully
2024-01-15 10:30:01 INFO  Loading configuration from /etc/app/config.yaml
2024-01-15 10:30:02 INFO  Database connection established
2024-01-15 10:30:02 DEBUG Initializing cache module
2024-01-15 10:30:03 DEBUG Cache module initialized
2024-01-15 10:30:03 INFO  Server listening on port 8080
2024-01-15 10:30:05 WARN  High memory usage detected: 85%
2024-01-15 10:30:10 ERROR Failed to process request: Connection timeout
2024-01-15 10:30:11 ERROR Failed to process request: Connection timeout
2024-01-15 10:30:12 ERROR Failed to process request: Connection timeout
2024-01-15 10:30:15 INFO  Request processed: GET /api/users
2024-01-15 10:30:16 INFO  Request processed: GET /api/users
2024-01-15 10:30:17 INFO  Request processed: GET /api/users
2024-01-15 10:30:20 DEBUG GC completed, freed 128MB
2024-01-15 10:30:25 ERROR Database query failed: timeout after 30s
"""

SYSLOG_STYLE = """Jan 15 10:30:01 server sshd[1234]: Accepted publickey for root
Jan 15 10:30:02 server sshd[1234]: Connection closed by 192.168.1.1
Jan 15 10:30:03 server kernel: [INFO] Memory usage normal
Jan 15 10:30:04 server kernel: [WARN] Disk space low
"""


class TestLogCompressor:
    """日志压缩器测试类"""

    def test_basic_log_compression(self, compressor):
        """测试基本日志压缩"""
        result = compressor.compress(SAMPLE_LOGS, ratio=0.5)

        assert result
        assert len(result) < len(SAMPLE_LOGS)

    def test_pattern_deduplication(self, compressor):
        """测试模式去重"""
        result = compressor.compress(SAMPLE_LOGS, ratio=0.5)

        assert result
        # 重复的ERROR行应被合并
        # 查找 [x3] 或类似标记
        assert "[x3]" in result or result.count("Connection timeout") <= 3

    def test_level_filtering(self, compressor):
        """测试日志级别过滤"""
        result = compressor.compress(SAMPLE_LOGS, ratio=0.3)

        assert result
        # 高压缩率时应主要保留ERROR
        lines = result.strip().split('\n')
        error_lines = [l for l in lines if 'ERROR' in l]
        assert len(error_lines) > 0

    def test_timestamp_normalization(self, compressor):
        """测试时间戳标准化"""
        result = compressor.compress(SAMPLE_LOGS, ratio=0.5)

        assert result
        # 时间戳应被标准化
        assert "[T]" in result

    def test_error_preservation(self, compressor):
        """测试错误日志保留"""
        result = compressor.compress(SAMPLE_LOGS, ratio=0.5)

        assert result
        assert "ERROR" in result

    def test_empty_input(self, compressor):
        """测试空输入"""
        assert compressor.compress("", ratio=0.5) == ""
        assert compressor.compress("   ", ratio=0.5) == ""

    def test_syslog_format(self, compressor):
        """测试syslog格式日志"""
        result = compressor.compress(SYSLOG_STYLE, ratio=0.5)

        assert result
        assert len(result) < len(SYSLOG_STYLE)

    def test_single_line_log(self, compressor):
        """测试单行日志"""
        text = "2024-01-15 10:30:01 INFO  Single log line"
        result = compressor.compress(text, ratio=0.5)

        assert result
        assert "INFO" in result

    def test_high_compression(self, compressor):
        """测试高压缩率"""
        result = compressor.compress(SAMPLE_LOGS, ratio=0.1)

        assert result
        # 高压缩率应大幅减少内容
        assert len(result) < len(SAMPLE_LOGS) * 0.5

    def test_log_level_extraction(self, compressor):
        """测试日志级别提取"""
        line = "2024-01-15 10:30:01 ERROR Something went wrong"
        parsed = compressor._parse_log_line(line)

        assert parsed["level"] == "error"
        assert parsed["has_timestamp"] is True
