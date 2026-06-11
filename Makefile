.PHONY: install dev test lint format clean serve

# 默认目标
all: install

# 安装项目
install:
	pip install -e .

# 开发环境安装
dev:
	pip install -e ".[dev,web]"

# 运行测试
test:
	python -m pytest tests/ -v --cov=tokensqueezer

# 代码检查
lint:
	flake8 tokensqueezer/ tests/
	mypy tokensqueezer/

# 代码格式化
format:
	black tokensqueezer/ tests/
	isort tokensqueezer/ tests/

# 清理构建产物
clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# 启动Web面板
serve:
	python -m tokensqueezer serve

# 快速验证
check: lint test
