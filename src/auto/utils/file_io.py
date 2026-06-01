"""
文件 IO 操作模块 - 文件读写、目录管理等。

提供文件和目录操作的便利函数，包括：
- JSON 文件读写
- YAML 文件读写
- 目录创建和清理
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .logger import logger


def read_json(file_path: str) -> Dict:
    """
    读取 JSON 文件。

    Args:
        file_path: 文件路径

    Returns:
        JSON 数据字典

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 格式错误
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"成功读取 JSON 文件: {file_path}")
        return data
    except Exception as e:
        logger.error(f"读取 JSON 文件失败: {file_path}, 错误: {e}")
        raise


def write_json(file_path: str, data: Dict, pretty: bool = True) -> None:
    """
    写入 JSON 文件。

    Args:
        file_path: 文件路径
        data: 要写入的数据
        pretty: 是否格式化输出，默认为 True

    Raises:
        IOError: 写入失败
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False)

        logger.info(f"成功写入 JSON 文件: {file_path}")
    except Exception as e:
        logger.error(f"写入 JSON 文件失败: {file_path}, 错误: {e}")
        raise


def read_yaml(file_path: str) -> Dict:
    """
    读取 YAML 文件。

    Args:
        file_path: 文件路径

    Returns:
        YAML 数据字典

    Raises:
        FileNotFoundError: 文件不存在
        yaml.YAMLError: YAML 格式错误
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        logger.info(f"成功读取 YAML 文件: {file_path}")
        return data
    except Exception as e:
        logger.error(f"读取 YAML 文件失败: {file_path}, 错误: {e}")
        raise


def write_yaml(file_path: str, data: Dict) -> None:
    """
    写入 YAML 文件。

    Args:
        file_path: 文件路径
        data: 要写入的数据

    Raises:
        IOError: 写入失败
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        logger.info(f"成功写入 YAML 文件: {file_path}")
    except Exception as e:
        logger.error(f"写入 YAML 文件失败: {file_path}, 错误: {e}")
        raise


def create_directory(dir_path: str) -> Path:
    """
    创建目录。

    Args:
        dir_path: 目录路径

    Returns:
        Path 对象

    Raises:
        OSError: 创建失败
    """
    try:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"目录创建成功: {dir_path}")
        return path
    except Exception as e:
        logger.error(f"创建目录失败: {dir_path}, 错误: {e}")
        raise


def clean_directory(dir_path: str) -> None:
    """
    清空目录中的所有文件。

    Args:
        dir_path: 目录路径

    Raises:
        FileNotFoundError: 目录不存在
    """
    try:
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {dir_path}")

        for item in path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                import shutil

                shutil.rmtree(item)

        logger.info(f"目录清空成功: {dir_path}")
    except Exception as e:
        logger.error(f"清空目录失败: {dir_path}, 错误: {e}")
        raise


def list_files(dir_path: str, pattern: str = "*") -> List[Path]:
    """
    列出目录中的文件。

    Args:
        dir_path: 目录路径
        pattern: 文件模式，默认 "*"（所有文件）

    Returns:
        文件路径列表

    Raises:
        FileNotFoundError: 目录不存在
    """
    try:
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"目录不存在: {dir_path}")

        files = list(path.glob(pattern))
        logger.info(f"找到 {len(files)} 个文件: {dir_path}")
        return files
    except Exception as e:
        logger.error(f"列出文件失败: {dir_path}, 错误: {e}")
        raise


__all__ = ["read_json", "write_json", "read_yaml", "write_yaml", "create_directory", "clean_directory", "list_files"]
