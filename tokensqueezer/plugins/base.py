"""
插件基类和注册机制

提供插件系统的抽象基类、注册/发现机制和自定义压缩器插件接口。
"""

import importlib
import inspect
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class PluginBase(ABC):
    """插件抽象基类

    所有TokenSqueezer插件必须继承此类。
    插件可以扩展压缩器、添加新的内容类型检测或提供自定义功能。
    """

    # 插件名称
    name: str = "base_plugin"
    # 插件版本
    version: str = "1.0.0"
    # 插件描述
    description: str = ""

    @abstractmethod
    def initialize(self, context: dict) -> None:
        """初始化插件

        Args:
            context: 插件上下文，包含引擎实例等共享对象
        """
        ...

    @abstractmethod
    def teardown(self) -> None:
        """清理插件资源"""
        ...

    def on_compress_start(self, text: str, content_type: str) -> Optional[str]:
        """压缩开始前的钩子

        Args:
            text: 输入文本
            content_type: 内容类型

        Returns:
            如果返回字符串，则替换原始文本；返回None则不做修改
        """
        return None

    def on_compress_end(self, result: Any) -> Any:
        """压缩结束后的钩子

        Args:
            result: 压缩结果

        Returns:
            修改后的结果
        """
        return result

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, version={self.version})>"


class PluginRegistry:
    """插件注册表

    管理插件的注册、发现和生命周期。
    """

    def __init__(self):
        """初始化插件注册表"""
        self._plugins: dict[str, PluginBase] = {}
        self._initialized: set[str] = set()
        self._context: dict = {}

    def register(self, plugin: PluginBase) -> None:
        """注册插件

        Args:
            plugin: 插件实例

        Raises:
            ValueError: 当插件名称已存在时
        """
        if plugin.name in self._plugins:
            raise ValueError(f"插件 '{plugin.name}' 已注册")

        self._plugins[plugin.name] = plugin

    def unregister(self, name: str) -> None:
        """注销插件

        Args:
            name: 插件名称
        """
        if name in self._initialized:
            self._plugins[name].teardown()
            self._initialized.discard(name)

        self._plugins.pop(name, None)

    def get(self, name: str) -> Optional[PluginBase]:
        """获取插件

        Args:
            name: 插件名称

        Returns:
            插件实例，如果不存在则返回None
        """
        return self._plugins.get(name)

    def initialize_all(self, context: Optional[dict] = None) -> None:
        """初始化所有已注册的插件

        Args:
            context: 插件上下文
        """
        self._context = context or {}

        for name, plugin in self._plugins.items():
            if name not in self._initialized:
                try:
                    plugin.initialize(self._context)
                    self._initialized.add(name)
                except Exception as e:
                    # 初始化失败的插件不阻塞其他插件
                    print(f"插件 '{name}' 初始化失败: {e}")

    def teardown_all(self) -> None:
        """清理所有已初始化的插件"""
        for name in list(self._initialized):
            try:
                self._plugins[name].teardown()
            except Exception:
                pass
            self._initialized.discard(name)

    def discover_plugins(self, directory: str) -> list[str]:
        """从目录中发现插件

        扫描指定目录中的Python模块，查找PluginBase的子类并自动注册。

        Args:
            directory: 插件目录路径

        Returns:
            发现的插件名称列表
        """
        plugin_dir = Path(directory)
        if not plugin_dir.exists() or not plugin_dir.is_dir():
            return []

        discovered: list[str] = []

        for py_file in plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            module_name = py_file.stem

            try:
                # 动态导入模块
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{module_name}",
                    str(py_file)
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # 查找PluginBase子类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            inspect.isclass(attr)
                            and issubclass(attr, PluginBase)
                            and attr is not PluginBase
                        ):
                            plugin_instance = attr()
                            self.register(plugin_instance)
                            discovered.append(plugin_instance.name)

            except Exception as e:
                print(f"加载插件 '{module_name}' 失败: {e}")

        return discovered

    @property
    def plugins(self) -> dict[str, PluginBase]:
        """获取所有已注册的插件"""
        return dict(self._plugins)

    @property
    def initialized_plugins(self) -> set[str]:
        """获取已初始化的插件名称集合"""
        return set(self._initialized)

    @property
    def plugin_count(self) -> int:
        """获取已注册插件数量"""
        return len(self._plugins)

    def list_plugins(self) -> list[dict]:
        """列出所有插件信息

        Returns:
            插件信息列表
        """
        return [
            {
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "initialized": p.name in self._initialized,
            }
            for p in self._plugins.values()
        ]
