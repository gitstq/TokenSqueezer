"""TokenSqueezer 安装脚本"""
from setuptools import setup, find_packages

setup(
    packages=find_packages(include=["tokensqueezer", "tokensqueezer.*"]),
    package_data={
        "tokensqueezer": ["web/templates/*.html"],
        "tokensqueezer": ["assets/*"],
    },
)
