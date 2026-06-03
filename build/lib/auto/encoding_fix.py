"""
编码修复模块 - 在项目启动时立即修复 Windows PowerShell 编码问题。

此模块在被导入时会自动执行编码修复，无需手动调用 fix_encoding()。
建议在项目的入口处最早导入此模块。
"""

import os
import sys

# Python 编码相关环境变量
# noinspection SpellCheckingInspection
PYTHON_IO_ENCODING = 'PYTHONIOENCODING'
LANG_ENV = 'LANG'
LC_ALL_ENV = 'LC_ALL'


def fix_encoding():
    """
    修复 Windows PowerShell 中文编码问题。

    这个函数会在模块导入时自动执行。
    不修改 sys.stdout，避免与 pytest 捕获机制冲突。
    """
    # 设置环境变量
    os.environ[PYTHON_IO_ENCODING] = 'utf-8'
    os.environ[LANG_ENV] = 'en_US.UTF-8'
    os.environ[LC_ALL_ENV] = 'en_US.UTF-8'

    # Windows 特殊处理：设置控制台代码页为 UTF-8
    if sys.platform == 'win32':
        # noinspection PyBroadException
        try:
            import subprocess
            # 尝试执行 chcp 65001 命令（设置代码页为 UTF-8）
            subprocess.run('chcp 65001', shell=True, capture_output=True)
        except Exception:
            pass


# 模块导入时自动执行修复
fix_encoding()

__all__ = ["fix_encoding"]

