"""
配置管理模块 - 统一读取和加载 YAML 配置。

该模块实现配置的集中管理，支持多环境配置加载和合并。
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Settings:
    """
    配置管理类 - 负责加载、合并和管理配置。

    支持从 YAML 文件读取配置，并支持环境变量覆盖。
    配置优先级：环境变量 > 特定环境配置 > 公共配置。
    """

    def __init__(self, env: str = "dev"):
        """
        初始化配置管理器。

        Args:
            env: 环境名称，默认为 "dev"。支持 dev、qa、prod。
        """
        self.env = env
        self.config_dir = Path(__file__).parent
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """
        加载配置文件。

        优先级：base.yaml -> {env}.yaml
        先加载公共配置，再加载特定环境配置（会覆盖公共配置）。
        """
        # 1. 加载公共配置
        base_path = self.config_dir / "base.yaml"
        if base_path.exists():
            with open(base_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}

        # 2. 加载环境特定配置并合并
        env_path = self.config_dir / f"{self.env}.yaml"
        if env_path.exists():
            with open(env_path, "r", encoding="utf-8") as f:
                env_config = yaml.safe_load(f) or {}
                self._config = self._merge_dict(self._config, env_config)

    @staticmethod
    def _merge_dict(base: Dict, override: Dict) -> Dict:
        """
        合并两个字典，覆盖配置优先。

        Args:
            base: 基础字典
            override: 覆盖字典

        Returns:
            合并后的字典
        """
        result = base.copy()
        for key, value in override.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = Settings._merge_dict(result[key], value)
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        获取配置值，支持点号分隔的嵌套键。

        Args:
            key: 配置键，支持点号分隔（如 "browser.headless"）
            default: 默认值

        Returns:
            配置值或默认值

        Example:
            >>> settings.get("browser.headless")
            False
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_dict(self, section: str) -> Dict:
        """
        获取配置段。

        Args:
            section: 配置段名称

        Returns:
            配置段字典
        """
        return self._config.get(section, {})

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问。"""
        return self.get(key)

    def __repr__(self) -> str:
        """配置对象字符串表示。"""
        return f"<Settings env={self.env}>"


# 全局配置单例
_settings_instance: Optional[Settings] = None


def get_settings(env: Optional[str] = None) -> Settings:
    """
    获取全局配置实例（单例模式）。

    Args:
        env: 环境名称，仅在首次调用时有效

    Returns:
        Settings 实例
    """
    global _settings_instance

    if _settings_instance is None:
        env = env or os.getenv("TEST_ENV", "dev")
        _settings_instance = Settings(env)

    return _settings_instance


# 为了向后兼容，导出主要类和函数
__all__ = ["Settings", "get_settings"]
