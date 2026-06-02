"""
auto 自动化测试包。
"""

from .api import LoginAPI, UserAPI
from .core import BaseAPI, BasePage
from .pages import BaiduSearchPage, HomePage

__all__ = [
    "BaseAPI",
    "BasePage",
    "LoginAPI",
    "UserAPI",
    "BaiduSearchPage",
    "HomePage",
]
