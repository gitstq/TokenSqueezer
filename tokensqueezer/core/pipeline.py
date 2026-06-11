"""
压缩管线

提供多步骤压缩流程编排，支持链式压缩和自定义管线。
"""

from typing import Optional

from .compressor import CompressionEngine, CompressionResult
from .content_detector import ContentType
from .token_counter import TokenCounter


class CompressionPipeline:
    """压缩管线

    支持多步骤链式压缩，每一步可以使用不同的压缩器。
    """

    def __init__(
        self,
        engine: Optional[CompressionEngine] = None,
        token_counter: Optional[TokenCounter] = None,
    ):
        """初始化压缩管线

        Args:
            engine: 压缩引擎实例，如果为None则创建默认引擎
            token_counter: Token计数器实例
        """
        self._token_counter = token_counter or TokenCounter()
        self._engine = engine or CompressionEngine(token_counter=self._token_counter)
        self._steps: list[dict] = []
        self._results: list[CompressionResult] = []

    def add_step(
        self,
        content_type: Optional[ContentType] = None,
        ratio: float = 0.5,
        name: str = "",
    ) -> "CompressionPipeline":
        """添加压缩步骤

        Args:
            content_type: 指定内容类型，如果为None则自动检测
            ratio: 目标压缩率
            name: 步骤名称

        Returns:
            self，支持链式调用
        """
        self._steps.append({
            "content_type": content_type,
            "ratio": ratio,
            "name": name or f"步骤{len(self._steps) + 1}",
        })
        return self

    def run(self, text: str) -> CompressionResult:
        """执行压缩管线

        如果没有定义步骤，则使用引擎默认行为进行单次压缩。

        Args:
            text: 输入文本

        Returns:
            最终的压缩结果

        Raises:
            ValueError: 当文本为空时
        """
        if not text or not text.strip():
            raise ValueError("输入文本不能为空")

        self._results = []

        # 如果没有定义步骤，执行单次压缩
        if not self._steps:
            return self._engine.compress(text)

        current_text = text
        final_result = None

        for step in self._steps:
            result = self._engine.compress(
                current_text,
                content_type=step["content_type"],
                ratio=step["ratio"],
            )
            self._results.append(result)
            current_text = result.compressed_text
            final_result = result

        # 构建最终结果（基于原始输入和最终输出）
        original_tokens = self._token_counter.count(text)
        compressed_tokens = self._token_counter.count(current_text)

        if final_result:
            final_result = CompressionResult(
                original_text=text,
                compressed_text=current_text,
                original_tokens=original_tokens,
                compressed_tokens=compressed_tokens,
                ratio=compressed_tokens / original_tokens if original_tokens > 0 else 1.0,
                saved_tokens=original_tokens - compressed_tokens,
                elapsed_time=sum(r.elapsed_time for r in self._results),
                content_type=self._results[0].content_type,
                compressor_name="pipeline",
            )

        return final_result

    @property
    def results(self) -> list[CompressionResult]:
        """获取每一步的压缩结果"""
        return self._results

    @property
    def step_count(self) -> int:
        """获取步骤数量"""
        return len(self._steps)

    def clear(self) -> "CompressionPipeline":
        """清空管线步骤

        Returns:
            self，支持链式调用
        """
        self._steps = []
        self._results = []
        return self

    def summary(self) -> str:
        """生成管线执行摘要

        Returns:
            摘要字符串
        """
        if not self._results:
            return "管线尚未执行"

        lines = [f"压缩管线执行摘要 ({len(self._results)} 步):"]
        total_saved = 0
        for i, result in enumerate(self._results):
            step_name = self._steps[i]["name"] if i < len(self._steps) else f"步骤{i+1}"
            lines.append(
                f"  {step_name}: {result.original_tokens} -> "
                f"{result.compressed_tokens} tokens "
                f"(节省 {result.saved_tokens}, 耗时 {result.elapsed_time:.4f}s)"
            )
            total_saved += result.saved_tokens

        lines.append(f"  总计节省: {total_saved} tokens")
        return "\n".join(lines)
