"""
配置管理

支持YAML/TOML配置文件、环境变量覆盖和默认配置。
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Config:
    """TokenSqueezer配置管理

    支持以下配置优先级（从高到低）：
    1. 环境变量
    2. 配置文件（YAML/TOML）
    3. 默认配置

    Attributes:
        encoding: tiktoken编码名称
        default_ratio: 默认压缩率
        web_host: Web面板监听地址
        web_port: Web面板监听端口
        max_input_length: 最大输入长度
        verbose: 是否详细输出
    """

    # Token计数配置
    encoding: str = "cl100k_base"

    # 压缩配置
    default_ratio: float = 0.5
    max_input_length: int = 1000000

    # Web面板配置
    web_host: str = "0.0.0.0"
    web_port: int = 8080

    # 输出配置
    verbose: bool = False
    output_format: str = "text"

    # 插件配置
    plugins_dir: str = ""
    auto_load_plugins: bool = False

    def __post_init__(self) -> None:
        """初始化后加载环境变量覆盖"""
        self._load_env_overrides()

    def _load_env_overrides(self) -> None:
        """从环境变量加载配置覆盖

        环境变量前缀: TOKENSQUEEZER_
        """
        env_mapping = {
            "TOKENSQUEEZER_ENCODING": "encoding",
            "TOKENSQUEEZER_DEFAULT_RATIO": "default_ratio",
            "TOKENSQUEEZER_WEB_HOST": "web_host",
            "TOKENSQUEEZER_WEB_PORT": "web_port",
            "TOKENSQUEEZER_VERBOSE": "verbose",
            "TOKENSQUEEZER_OUTPUT_FORMAT": "output_format",
            "TOKENSQUEEZER_PLUGINS_DIR": "plugins_dir",
            "TOKENSQUEEZER_AUTO_LOAD_PLUGINS": "auto_load_plugins",
        }

        for env_var, attr_name in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                setattr(self, attr_name, self._parse_env_value(value, attr_name))

    def _parse_env_value(self, value: str, attr_name: str) -> Any:
        """解析环境变量值

        Args:
            value: 环境变量字符串值
            attr_name: 对应的属性名

        Returns:
            解析后的值
        """
        # 布尔值
        if attr_name in ("verbose", "auto_load_plugins"):
            return value.lower() in ("true", "1", "yes", "on")

        # 数值
        if attr_name in ("default_ratio", "web_port", "max_input_length"):
            try:
                return int(value) if attr_name == "web_port" else float(value)
            except ValueError:
                return value

        return value

    @classmethod
    def from_file(cls, path: str) -> "Config":
        """从配置文件加载配置

        支持YAML和TOML格式。

        Args:
            path: 配置文件路径

        Returns:
            Config实例
        """
        config = cls()
        file_path = Path(path)

        if not file_path.exists():
            return config

        suffix = file_path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            config_data = cls._load_yaml(file_path)
        elif suffix == ".toml":
            config_data = cls._load_toml(file_path)
        else:
            return config

        if config_data:
            for key, value in config_data.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        return config

    @staticmethod
    def _load_yaml(path: Path) -> dict:
        """加载YAML配置文件

        Args:
            path: YAML文件路径

        Returns:
            配置字典
        """
        try:
            import yaml
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            return {}
        except Exception:
            return {}

    @staticmethod
    def _load_toml(path: Path) -> dict:
        """加载TOML配置文件

        Args:
            path: TOML文件路径

        Returns:
            配置字典
        """
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib
            except ImportError:
                return {}

        try:
            with open(path, "rb") as f:
                return tomllib.load(f) or {}
        except Exception:
            return {}

    def to_dict(self) -> dict:
        """将配置转换为字典

        Returns:
            配置字典
        """
        return {
            "encoding": self.encoding,
            "default_ratio": self.default_ratio,
            "max_input_length": self.max_input_length,
            "web_host": self.web_host,
            "web_port": self.web_port,
            "verbose": self.verbose,
            "output_format": self.output_format,
            "plugins_dir": self.plugins_dir,
            "auto_load_plugins": self.auto_load_plugins,
        }
