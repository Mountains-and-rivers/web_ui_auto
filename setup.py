"""
项目安装脚本 - 将项目安装为 Python 包

安装后可以直接导入所有模块，无需配置 PYTHONPATH
"""
from setuptools import setup

setup(
    name="web-ui-auto",
    version="1.0.0",
    description="基于 Playwright + Pytest 的 Web UI 自动化测试框架",
    author="Author",
    author_email="author@example.com",
    
    # 明确指定所有包
    packages=[
        "auto",
        "auto.api",
        "auto.core",
        "auto.pages",
        "auto.utils",
        "config",
        "fixtures",
        "testdata",
    ],
    
    # 指定包的目录映射
    package_dir={
        "auto": "src/auto",
        "config": "config",
        "fixtures": "fixtures",
        "testdata": "testdata",
    },
    
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.40.0",
        "pytest>=7.4.0",
        "pytest-html>=4.0.0",
        "allure-pytest>=2.13.0",
        "pyyaml>=6.0",
        "loguru>=0.7.0",
    ],
    extras_require={
        "dev": [
            "setuptools>=45",
            "wheel>=0.38.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "isort>=5.12.0",
        ]
    },
    
    # 添加命令行入口点
    entry_points={
        "console_scripts": [
            "web-ui-auto=auto.main:main",
        ],
    },
    
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
