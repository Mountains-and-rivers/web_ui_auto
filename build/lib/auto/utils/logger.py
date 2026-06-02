"""
日志管理模块 - 统一的日志记录封装。

提供日志记录功能，支持：
- 按天切割日志文件
- 控制台和文件同时输出
- 多级别日志控制
"""

import sys
from pathlib import Path

from loguru import logger as _logger

# 日志输出目录
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 移除默认处理器
_logger.remove()

# 添加控制台输出（不使用彩色，避免编码问题）
_logger.add(
    sys.stdout,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    colorize=False,
)

# 添加文件输出（按天切割）
_logger.add(
    str(LOG_DIR / "framework" / "{time:YYYY-MM-DD}.log"),
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="00:00",  # 每天午夜切割
    retention="7 days",  # 保留 7 天日志
)

# 为向后兼容，导出 logger
logger = _logger

__all__ = ["logger"]
