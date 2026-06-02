"""
数据库 fixture 模块（示例）。

提供数据库相关的 fixture，如连接、清理等。
"""

import pytest


@pytest.fixture
def db_connection():
    """
    数据库连接 fixture。

    示例：数据库连接初始化和清理。

    Yields:
        数据库连接对象
    """
    # 初始化数据库连接
    print("初始化数据库连接")
    connection = None

    yield connection

    # 清理数据库连接
    print("关闭数据库连接")


__all__ = ["db_connection"]
