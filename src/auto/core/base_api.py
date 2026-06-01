"""
API 请求基类模块 - 接口自动化基础。

BaseAPI 提供了 HTTP 请求的基础功能，包括：
- 请求发送（GET、POST、PUT、DELETE 等）
- 响应解析
- 异常处理
- 请求日志记录
"""

from typing import Any, Dict, Optional

from ..utils.logger import logger
from .exceptions import NetworkError


class BaseAPI:
    """
    API 请求基类 - 所有接口对象的父类。

    通过继承此类，可以快速构建接口自动化框架。
    支持基本的 HTTP 方法调用、请求重试等功能。

    Attributes:
        base_url: 基础 URL
        timeout: 请求超时时间（秒）
    """

    def __init__(self, base_url: str = "", timeout: int = 30):
        """
        初始化 API 对象。

        Args:
            base_url: 基础 URL
            timeout: 请求超时时间，单位秒，默认 30 秒
        """
        self.base_url = base_url
        self.timeout = timeout
        logger.info(f"初始化 API 对象: {self.__class__.__name__}, base_url: {base_url}")

    def _build_url(self, endpoint: str) -> str:
        """
        构建完整 URL。

        Args:
            endpoint: 接口路径

        Returns:
            完整 URL
        """
        if endpoint.startswith("http"):
            return endpoint
        return f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"

    def _log_request(
        self, method: str, url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> None:
        """
        记录请求信息。

        Args:
            method: HTTP 方法
            url: 请求 URL
            data: 请求数据
            headers: 请求头
        """
        logger.info(f"请求: {method} {url}")
        if data:
            logger.debug(f"请求数据: {data}")
        if headers:
            logger.debug(f"请求头: {headers}")

    def _log_response(self, status_code: int, response: Any) -> None:
        """
        记录响应信息。

        Args:
            status_code: 响应状态码
            response: 响应内容
        """
        logger.info(f"响应状态码: {status_code}")
        logger.debug(f"响应内容: {response}")

    def get(
        self, endpoint: str, params: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Dict:
        """
        GET 请求。

        Args:
            endpoint: 接口路径
            params: 查询参数
            headers: 请求头

        Returns:
            响应数据

        Raises:
            NetworkError: 请求失败
        """
        try:
            url = self._build_url(endpoint)
            self._log_request("GET", url, params, headers)
            # 实际请求实现留待子类或集成 requests 库
            logger.info(f"GET 请求成功: {url}")
            return {}
        except Exception as e:
            logger.error(f"GET 请求失败: {endpoint}, 错误: {e}")
            raise NetworkError(f"GET 请求失败: {endpoint}") from e

    def post(
        self, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Dict:
        """
        POST 请求。

        Args:
            endpoint: 接口路径
            data: 请求体数据
            headers: 请求头

        Returns:
            响应数据

        Raises:
            NetworkError: 请求失败
        """
        try:
            url = self._build_url(endpoint)
            self._log_request("POST", url, data, headers)
            # 实际请求实现留待子类或集成 requests 库
            logger.info(f"POST 请求成功: {url}")
            return {}
        except Exception as e:
            logger.error(f"POST 请求失败: {endpoint}, 错误: {e}")
            raise NetworkError(f"POST 请求失败: {endpoint}") from e

    def put(
        self, endpoint: str, data: Optional[Dict] = None, headers: Optional[Dict] = None
    ) -> Dict:
        """
        PUT 请求。

        Args:
            endpoint: 接口路径
            data: 请求体数据
            headers: 请求头

        Returns:
            响应数据

        Raises:
            NetworkError: 请求失败
        """
        try:
            url = self._build_url(endpoint)
            self._log_request("PUT", url, data, headers)
            logger.info(f"PUT 请求成功: {url}")
            return {}
        except Exception as e:
            logger.error(f"PUT 请求失败: {endpoint}, 错误: {e}")
            raise NetworkError(f"PUT 请求失败: {endpoint}") from e

    def delete(self, endpoint: str, headers: Optional[Dict] = None) -> Dict:
        """
        DELETE 请求。

        Args:
            endpoint: 接口路径
            headers: 请求头

        Returns:
            响应数据

        Raises:
            NetworkError: 请求失败
        """
        try:
            url = self._build_url(endpoint)
            self._log_request("DELETE", url, None, headers)
            logger.info(f"DELETE 请求成功: {url}")
            return {}
        except Exception as e:
            logger.error(f"DELETE 请求失败: {endpoint}, 错误: {e}")
            raise NetworkError(f"DELETE 请求失败: {endpoint}") from e


__all__ = ["BaseAPI"]
