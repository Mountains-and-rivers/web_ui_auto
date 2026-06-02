"""
自定义异常模块 - 框架级异常定义。

定义自动化框架中常见的异常类，用于更精细的错误处理和日志记录。
"""


class AutoTestException(Exception):
    """
    自动化测试框架基础异常。

    所有框架级异常都应该继承此异常。
    """

    pass


class ElementNotFoundError(AutoTestException):
    """
    元素未找到异常。

    在指定的超时时间内未能找到指定的页面元素。
    """

    pass


class TimeoutError(AutoTestException):
    """
    超时异常。

    操作在规定时间内未能完成。
    """

    pass


class LoginFailureError(AutoTestException):
    """
    登录失败异常。

    登录操作失败，无法获取有效的会话。
    """

    pass


class NetworkError(AutoTestException):
    """
    网络错误异常。

    网络连接异常或服务器无法访问。
    """

    pass


class AssertionError(AutoTestException):
    """
    断言失败异常。

    测试断言验证失败。
    """

    pass


__all__ = [
    "AutoTestException",
    "ElementNotFoundError",
    "TimeoutError",
    "LoginFailureError",
    "NetworkError",
    "AssertionError",
]
