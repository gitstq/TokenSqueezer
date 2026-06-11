# TokenSqueezer

智能LLM Token压缩工具 - 减少60-95%的Token消耗

## 特性

- 多种内容类型智能压缩（文本、JSON、代码、Markdown、日志）
- 基于tiktoken的精确Token计数
- 内置Web可视化面板
- 插件化架构，支持自定义压缩器
- 离线优先，无需网络连接
- CLI和Web双模式

## 安装

```bash
pip install -e .
```

## 快速开始

### CLI模式

```bash
# 压缩文本
tokensqueezer text "你的长文本内容..."

# 压缩文件
tokensqueezer compress input.txt -o output.txt

# 压缩JSON
tokensqueezer json data.json

# 启动Web面板
tokensqueezer serve
```

### Python API

```python
from tokensqueezer import compress

result = compress("你的长文本内容...")
print(result.compressed_text)
print(f"压缩率: {result.ratio:.1%}")
```

## Web面板

```bash
tokensqueezer serve --port 8080
```

访问 http://localhost:8080 查看Web面板。

## 许可证

MIT License
