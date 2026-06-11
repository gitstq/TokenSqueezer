# 贡献指南

感谢你对 TokenSqueezer 的关注！以下是参与贡献的指南。

## 开发环境设置

1. 克隆仓库
2. 安装开发依赖：`pip install -e ".[dev,web]"`
3. 运行测试：`make test`

## 代码规范

- 使用 Python 3.9+ 语法
- 所有函数必须有类型注解和 docstring
- 遵循 PEP 8 风格（使用 black 和 isort 格式化）
- 通过 flake8 和 mypy 检查

## 提交 PR

1. Fork 仓库
2. 创建特性分支
3. 编写代码和测试
4. 确保所有测试通过
5. 提交 Pull Request

## 添加新压缩器

1. 在 `tokensqueezer/compressors/` 下创建新文件
2. 继承 `CompressorBase` 基类
3. 实现 `compress` 方法
4. 在 `tokensqueezer/compressors/__init__.py` 中注册
5. 添加对应的测试文件

## 问题反馈

请通过 GitHub Issues 提交 Bug 报告或功能建议。
