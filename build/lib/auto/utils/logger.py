"""
日志管理模块 - 统一的日志记录封装。

提供日志记录功能，支持：
- 按天切割日志文件
- 控制台和文件同时输出
- 多级别日志控制
- 框架日志和用例日志分离
"""

import sys
from pathlib import Path

from loguru import logger as _logger

# 日志输出目录
LOG_DIR = Path(__file__).parent.parent.parent.parent / "logs"
FRAMEWORK_LOG_DIR = LOG_DIR / "framework"
CASES_LOG_DIR = LOG_DIR / "cases"

# 确保日志目录存在（使用绝对路径）
LOG_DIR.mkdir(parents=True, exist_ok=True)
FRAMEWORK_LOG_DIR.mkdir(parents=True, exist_ok=True)
CASES_LOG_DIR.mkdir(parents=True, exist_ok=True)

# 移除默认处理器
_logger.remove()

# 添加控制台输出（不使用彩色，避免编码问题）
_logger.add(
    sys.stdout,
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    colorize=False,
)

# 添加框架日志文件输出（按天切割）
_logger.add(
    str(FRAMEWORK_LOG_DIR / "{time:YYYY-MM-DD}.log"),
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    rotation="00:00",  # 每天午夜切割
    retention="7 days",  # 保留 7 天日志
)


def get_case_logger(case_name: str):
    """获取用例级别的日志记录器。
    
    Args:
        case_name: 用例名称，用于生成独立的日志文件
        
    Returns:
        Logger 实例，日志会写入到 cases/{case_name}/{time}.log
    """
    # 为每个用例创建独立的日志目录
    case_log_dir = CASES_LOG_DIR / case_name
    case_log_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建新的 logger 实例
    case_logger = _logger.bind(case=case_name)
    
    # 为该用例添加独立的文件处理器
    case_logger.add(
        str(case_log_dir / "{time:YYYY-MM-DD_HH-mm-ss}.log"),
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="00:00",
        retention="7 days",
    )
    
    return case_logger


# 为向后兼容，导出默认 logger
logger = _logger

__all__ = ["logger", "get_case_logger"]
