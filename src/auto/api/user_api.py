"""
用户管理相关接口模块（示例）。

提供用户管理相关的 API 接口封装。
"""

from ..core.base_api import BaseAPI
from ..utils.logger import logger


class UserAPI(BaseAPI):
    """
    用户管理接口模块。

    Attributes:
        base_url: 基础 URL
    """

    def __init__(self, base_url: str = ""):
        """
        初始化用户 API。

        Args:
            base_url: 基础 URL
        """
        super().__init__(base_url)

    def get_user_info(self, user_id: str) -> dict:
        """
        获取用户信息。

        Args:
            user_id: 用户 ID

        Returns:
            用户信息
        """
        try:
            logger.info(f"获取用户信息: {user_id}")
            # response = self.get(f"/api/user/{user_id}")
            logger.info("获取用户信息成功")
            return {"code": 0, "msg": "成功"}
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            raise


__all__ = ["UserAPI"]
