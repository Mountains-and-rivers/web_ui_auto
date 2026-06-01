"""
通用工具模块 - 常用的辅助函数。

提供通用工具函数，包括：
- 随机数生成
- 时间相关函数
- 字符串加密/解密
- 等待函数
"""

import random
import string
import time
from typing import Any, List, Optional

from .logger import logger


def generate_random_string(length: int = 10, chars: Optional[str] = None) -> str:
    """
    生成随机字符串。

    Args:
        length: 字符串长度，默认 10
        chars: 字符集，默认为字母 + 数字

    Returns:
        随机字符串
    """
    if chars is None:
        chars = string.ascii_letters + string.digits

    result = "".join(random.choice(chars) for _ in range(length))
    logger.debug(f"生成随机字符串: {result}")
    return result


def generate_random_number(start: int = 0, end: int = 100) -> int:
    """
    生成随机数。

    Args:
        start: 范围开始（包含）
        end: 范围结束（包含）

    Returns:
        随机数
    """
    result = random.randint(start, end)
    logger.debug(f"生成随机数: {result}")
    return result


def wait_for_seconds(seconds: float) -> None:
    """
    等待指定秒数。

    Args:
        seconds: 等待时间（秒）
    """
    logger.info(f"等待 {seconds} 秒")
    time.sleep(seconds)


def retry_until_success(
    func, max_attempts: int = 3, delay: float = 1.0, *args, **kwargs
) -> Any:
    """
    重试函数直到成功。

    Args:
        func: 要执行的函数
        max_attempts: 最大尝试次数
        delay: 重试延迟（秒）
        *args: 函数位置参数
        **kwargs: 函数关键字参数

    Returns:
        函数返回值

    Raises:
        Exception: 所有尝试都失败
    """
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"尝试执行函数 {func.__name__}，第 {attempt} 次")
            result = func(*args, **kwargs)
            logger.info(f"函数执行成功: {func.__name__}")
            return result
        except Exception as e:
            last_error = e
            logger.warning(f"尝试 {attempt} 失败: {e}")
            if attempt < max_attempts:
                time.sleep(delay)

    logger.error(f"函数执行失败，已尝试 {max_attempts} 次")
    raise last_error


def get_current_timestamp() -> str:
    """
    获取当前时间戳（字符串格式）。

    Returns:
        时间戳字符串（格式：YYYY-MM-DD HH:mm:ss）
    """
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.debug(f"获取当前时间戳: {timestamp}")
    return timestamp


def get_current_date() -> str:
    """
    获取当前日期（字符串格式）。

    Returns:
        日期字符串（格式：YYYY-MM-DD）
    """
    from datetime import datetime

    date = datetime.now().strftime("%Y-%m-%d")
    logger.debug(f"获取当前日期: {date}")
    return date


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名。

    Args:
        file_path: 文件路径

    Returns:
        扩展名（带点）
    """
    from pathlib import Path

    ext = Path(file_path).suffix
    logger.debug(f"文件扩展名: {ext}")
    return ext


def is_email_valid(email: str) -> bool:
    """
    验证邮箱格式。

    Args:
        email: 邮箱地址

    Returns:
        邮箱格式是否有效
    """
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    is_valid = bool(re.match(pattern, email))
    logger.debug(f"邮箱验证: {email}, 结果: {is_valid}")
    return is_valid


def list_to_dict(items: List, key: str) -> dict:
    """
    将列表转换为字典。

    Args:
        items: 列表
        key: 用作字典键的字段名

    Returns:
        字典
    """
    result = {item.get(key): item for item in items if isinstance(item, dict) and key in item}
    logger.debug(f"列表转换为字典，共 {len(result)} 项")
    return result


__all__ = [
    "generate_random_string",
    "generate_random_number",
    "wait_for_seconds",
    "retry_until_success",
    "get_current_timestamp",
    "get_current_date",
    "get_file_extension",
    "is_email_valid",
    "list_to_dict",
]
