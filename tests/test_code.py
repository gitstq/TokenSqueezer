"""
代码压缩器测试
"""

import pytest

from tokensqueezer.compressors.code import CodeCompressor
from tokensqueezer.core.token_counter import TokenCounter


@pytest.fixture
def compressor():
    """创建代码压缩器实例"""
    counter = TokenCounter()
    return CodeCompressor(counter)


PYTHON_CODE = '''# 这是一个Python示例
import os
import sys

def hello_world():
    """打印Hello World"""
    print("Hello, World!")
    return True

class MyClass:
    """示例类"""
    def __init__(self):
        self.value = 42

    def get_value(self):
        return self.value
'''

JS_CODE = '''// JavaScript示例
const express = require('express');
const app = express();

// 创建路由
app.get('/', (req, res) => {
    res.send('Hello World');
});

// 启动服务器
app.listen(3000, () => {
    console.log('Server running on port 3000');
});
'''

GO_CODE = '''// Go示例
package main

import "fmt"

// 主函数
func main() {
    fmt.Println("Hello, World!")
}
'''

RUST_CODE = '''// Rust示例
fn main() {
    println!("Hello, World!");
}
'''

JAVA_CODE = '''// Java示例
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
'''

CPP_CODE = '''// C++示例
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
'''


class TestCodeCompressor:
    """代码压缩器测试类"""

    def test_python_comment_removal(self, compressor):
        """测试Python注释移除"""
        result = compressor.compress(PYTHON_CODE, ratio=0.5)

        assert result
        assert "# 这是一个Python示例" not in result

    def test_python_structure_preservation(self, compressor):
        """测试Python结构保留"""
        result = compressor.compress(PYTHON_CODE, ratio=0.5)

        assert result
        # 关键结构应保留
        assert "def hello_world" in result
        assert "class MyClass" in result
        assert "import" in result

    def test_javascript_compression(self, compressor):
        """测试JavaScript压缩"""
        result = compressor.compress(JS_CODE, ratio=0.5)

        assert result
        assert "// JavaScript" not in result
        assert "express" in result

    def test_go_compression(self, compressor):
        """测试Go代码压缩"""
        result = compressor.compress(GO_CODE, ratio=0.5)

        assert result
        assert "package main" in result
        assert "func main" in result

    def test_rust_compression(self, compressor):
        """测试Rust代码压缩"""
        result = compressor.compress(RUST_CODE, ratio=0.5)

        assert result
        assert "fn main" in result

    def test_java_compression(self, compressor):
        """测试Java代码压缩"""
        result = compressor.compress(JAVA_CODE, ratio=0.5)

        assert result
        assert "public static void main" in result

    def test_cpp_compression(self, compressor):
        """测试C++代码压缩"""
        result = compressor.compress(CPP_CODE, ratio=0.5)

        assert result
        assert "#include" in result
        assert "int main" in result

    def test_empty_input(self, compressor):
        """测试空输入"""
        assert compressor.compress("", ratio=0.5) == ""
        assert compressor.compress("   ", ratio=0.5) == ""

    def test_blank_line_removal(self, compressor):
        """测试空行移除"""
        code = "def foo():\n\n\n\n    pass\n\n\n"
        result = compressor.compress(code, ratio=0.5)

        assert result
        assert "\n\n\n" not in result

    def test_multiline_comment_removal(self, compressor):
        """测试多行注释移除"""
        code = '#include <iostream>\n\n/* 这是\n一个多行注释 */\nint x = 5;'
        result = compressor.compress(code, ratio=0.5)

        assert result
        assert "/*" not in result
        assert "多行注释" not in result
        assert "#include" in result
