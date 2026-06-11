"""压缩器模块"""
from .text import TextCompressor
from .json import JsonCompressor
from .code import CodeCompressor
from .markdown import MarkdownCompressor
from .log import LogCompressor

__all__ = [
    "TextCompressor",
    "JsonCompressor",
    "CodeCompressor",
    "MarkdownCompressor",
    "LogCompressor",
]
