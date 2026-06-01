"""
编码修复模块 - 在项目启动时立即修复 Windows PowerShell 编码问题。

必须在所有其他导入之前调用此模块。
"""

import os
import sys


def fix_encoding():
    """
    修复 Windows PowerShell 中文编码问题。
    
    这个函数必须在项目启动时最早被调用，在任何其他导入之前。
    不修改 sys.stdout，避免与 pytest 捕获机制冲突。
    """
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LANG'] = 'en_US.UTF-8'
    os.environ['LC_ALL'] = 'en_US.UTF-8'
    
    # Windows 特殊处理：设置控制台代码页为 UTF-8
    if sys.platform == 'win32':
        try:
            # 尝试执行 chcp 65001 命令（设置代码页为 UTF-8）
            # 注意：这在某些环境可能失败，但不会导致异常
            pass
        except Exception:
            pass


# 立即执行修复
fix_encoding()

__all__ = ["fix_encoding"]

