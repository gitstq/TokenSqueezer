"""
CLI命令定义

基于Click的命令行接口，提供compress、text、json、serve、stats等命令。
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .core.compressor import CompressionEngine, CompressionResult
from .core.content_detector import ContentType
from .core.token_counter import TokenCounter

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="TokenSqueezer")
def main():
    """TokenSqueezer - 智能LLM Token压缩工具

    减少60-95%的Token消耗，支持文本、JSON、代码、Markdown、日志等多种内容类型。
    """
    pass


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default=None, help="输出文件路径")
@click.option("-r", "--ratio", type=float, default=0.5, help="目标压缩率 (0.1-0.9)")
@click.option("-f", "--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("-v", "--verbose", is_flag=True, help="显示详细输出")
def compress(input: str, output: Optional[str], ratio: float, format: str, verbose: bool):
    """压缩文件或文本内容"""
    path = Path(input)

    if not path.exists():
        console.print(f"[red]错误: 文件不存在 - {input}[/red]")
        sys.exit(1)

    # 读取文件内容
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]错误: 无法读取文件 - {e}[/red]")
        sys.exit(1)

    if not content.strip():
        console.print("[yellow]警告: 文件内容为空[/yellow]")
        sys.exit(0)

    # 执行压缩
    engine = CompressionEngine()
    try:
        result = engine.compress(content, ratio=ratio)
    except ValueError as e:
        console.print(f"[red]错误: {e}[/red]")
        sys.exit(1)

    # 输出结果
    _output_result(result, output, format, verbose)


@main.command()
@click.argument("text")
@click.option("-o", "--output", type=click.Path(), default=None, help="输出文件路径")
@click.option("-r", "--ratio", type=float, default=0.5, help="目标压缩率 (0.1-0.9)")
@click.option("-f", "--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("-v", "--verbose", is_flag=True, help="显示详细输出")
def text(text: str, output: Optional[str], ratio: float, format: str, verbose: bool):
    """直接压缩文本内容"""
    engine = CompressionEngine()
    try:
        result = engine.compress(text, ratio=ratio)
    except ValueError as e:
        console.print(f"[red]错误: {e}[/red]")
        sys.exit(1)

    _output_result(result, output, format, verbose)


@main.command()
@click.argument("input", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), default=None, help="输出文件路径")
@click.option("-r", "--ratio", type=float, default=0.5, help="目标压缩率 (0.1-0.9)")
@click.option("-f", "--format", type=click.Choice(["text", "json"]), default="text", help="输出格式")
@click.option("-v", "--verbose", is_flag=True, help="显示详细输出")
def json(input: str, output: Optional[str], ratio: float, format: str, verbose: bool):
    """压缩JSON文件"""
    path = Path(input)

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        console.print(f"[red]错误: 无法读取文件 - {e}[/red]")
        sys.exit(1)

    engine = CompressionEngine()
    try:
        result = engine.compress(content, content_type=ContentType.JSON, ratio=ratio)
    except ValueError as e:
        console.print(f"[red]错误: {e}[/red]")
        sys.exit(1)

    _output_result(result, output, format, verbose)


@main.command()
@click.option("--host", default="0.0.0.0", help="监听地址")
@click.option("--port", default=8080, type=int, help="监听端口")
@click.option("--reload", is_flag=True, help="开发模式（自动重载）")
def serve(host: str, port: int, reload: bool):
    """启动Web可视化面板"""
    try:
        import uvicorn
    except ImportError:
        console.print("[red]错误: 需要安装Web依赖。运行 pip install fastapi uvicorn[/red]")
        sys.exit(1)

    console.print(
        Panel(
            f"[green]TokenSqueezer Web面板启动中...[/green]\n\n"
            f"  地址: [cyan]http://{host}:{port}[/cyan]\n"
            f"  按 Ctrl+C 停止服务",
            title="TokenSqueezer Web",
            border_style="blue",
        )
    )

    uvicorn.run(
        "tokensqueezer.web.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


@main.command()
@click.argument("input", type=click.Path(exists=True), required=False)
@click.option("-r", "--ratio", type=float, default=0.5, help="目标压缩率 (0.1-0.9)")
def stats(input: Optional[str], ratio: float):
    """显示压缩统计信息"""
    if input:
        path = Path(input)
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"[red]错误: 无法读取文件 - {e}[/red]")
            sys.exit(1)

        engine = CompressionEngine()
        try:
            result = engine.compress(content, ratio=ratio)
        except ValueError as e:
            console.print(f"[red]错误: {e}[/red]")
            sys.exit(1)

        _display_stats(result)
    else:
        # 显示引擎信息
        engine = CompressionEngine()
        table = Table(title="TokenSqueezer 压缩引擎信息")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="green")

        counter = TokenCounter()
        table.add_row("Token计数器", repr(counter))
        table.add_row("可用压缩器", str(len(engine.list_compressors())))

        for comp in engine.list_compressors():
            table.add_row(f"  - {comp['name']}", comp['description'])
            table.add_row("    支持类型", ", ".join(comp['supported_types']))

        console.print(table)


def _output_result(
    result: CompressionResult,
    output: Optional[str],
    format: str,
    verbose: bool,
) -> None:
    """输出压缩结果

    Args:
        result: 压缩结果
        output: 输出文件路径
        format: 输出格式
        verbose: 是否显示详细输出
    """
    if format == "json":
        output_data = {
            "original_tokens": result.original_tokens,
            "compressed_tokens": result.compressed_tokens,
            "ratio": round(result.ratio, 4),
            "saved_tokens": result.saved_tokens,
            "compression_percentage": round(result.compression_percentage, 2),
            "elapsed_time": round(result.elapsed_time, 6),
            "content_type": result.content_type.value,
            "compressor": result.compressor_name,
            "compressed_text": result.compressed_text,
        }
        output_str = json.dumps(output_data, ensure_ascii=False, indent=2)
    else:
        output_str = result.compressed_text

    # 输出到文件
    if output:
        try:
            Path(output).write_text(output_str, encoding="utf-8")
            console.print(f"[green]结果已保存到: {output}[/green]")
        except Exception as e:
            console.print(f"[red]错误: 无法写入文件 - {e}[/red]")
            sys.exit(1)
    else:
        # 输出到终端
        console.print(output_str)

    # 显示统计信息
    if verbose:
        _display_stats(result)


def _display_stats(result: CompressionResult) -> None:
    """显示压缩统计信息

    Args:
        result: 压缩结果
    """
    table = Table(title="压缩统计")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")

    table.add_row("内容类型", result.content_type.value)
    table.add_row("压缩器", result.compressor_name)
    table.add_row("原始Token", str(result.original_tokens))
    table.add_row("压缩后Token", str(result.compressed_tokens))
    table.add_row("节省Token", str(result.saved_tokens))
    table.add_row("压缩率", f"{result.ratio:.2%}")
    table.add_row("节省比例", f"{result.compression_percentage:.1f}%")
    table.add_row("耗时", f"{result.elapsed_time:.4f}s")

    console.print()
    console.print(table)
