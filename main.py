"""
命令行入口 - 使用argparse实现CLI工具
"""
import sys
import argparse
import subprocess
from pathlib import Path

from auto.utils.logger import logger, init_cli_logger


def _log_header(title: str):
    """打印分隔线标题。"""
    logger.info("=" * 60)
    logger.info(title)
    logger.info("=" * 60)


def run_tests(test_path, extra_args=None):
    """运行pytest测试"""
    cmd = [sys.executable, "-m", "pytest", test_path]
    if extra_args:
        cmd.extend(extra_args)
    else:
        cmd.extend(["-v", "--tb=short"])

    logger.info(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def cmd_run(args):
    """运行测试"""
    _log_header("Web UI Auto - 运行测试")

    extra_args = ["-v", "--tb=short"]
    if args.markers:
        extra_args.extend(["-m", args.markers])
    if args.html_report:
        extra_args.extend(["--html=reports/html-report.html", "--self-contained-html"])
    if args.allure_dir:
        extra_args.extend([f"--alluredir={args.allure_dir}"])

    return run_tests(args.test_path, extra_args)


def _run_marked_tests(title: str, marker: str):
    """运行带标记的测试。"""
    _log_header(title)
    return run_tests("tests/", ["-v", "-m", marker])


def cmd_smoke(args):
    """运行冒烟测试"""
    return _run_marked_tests("Web UI Auto - 运行冒烟测试", "smoke")


def cmd_critical(args):
    """运行关键路径测试"""
    return _run_marked_tests("Web UI Auto - 运行关键路径测试", "critical")


def cmd_api(args):
    """运行API测试"""
    return _run_marked_tests("Web UI Auto - 运行API测试", "api")


def cmd_ui(args):
    """运行UI测试"""
    return _run_marked_tests("Web UI Auto - 运行UI测试", "ui")


def cmd_report(args):
    """生成Allure报告"""
    _log_header("Web UI Auto - 生成Allure报告")

    report_dir = args.allure_dir or "reports/allure-results"
    run_tests("tests/", [f"--alluredir={report_dir}", "-v", "--tb=short"])

    logger.info("正在打开Allure报告...")
    subprocess.run(["allure", "serve", report_dir])


def cmd_clean(args):
    """清理缓存和报告"""
    _log_header("Web UI Auto - 清理缓存和报告")

    import shutil

    dirs_to_clean = [
        "__pycache__",
        ".pytest_cache",
        "build",
        "dist",
        "*.egg-info",
        "reports",
        "logs",
        "artifacts/screenshots",
        "artifacts/videos",
    ]

    for dir_name in dirs_to_clean:
        try:
            if "*" in dir_name:
                import glob
                for path in glob.glob(dir_name):
                    if Path(path).is_dir():
                        shutil.rmtree(path)
                        logger.info(f"已删除: {path}")
            else:
                path = Path(dir_name)
                if path.exists():
                    shutil.rmtree(path)
                    logger.info(f"已删除: {dir_name}")
        except Exception as e:
            logger.error(f"删除失败 {dir_name}: {e}")

    logger.info("清理完成！")
    return 0


def cmd_install_browser(args):
    """安装Playwright浏览器"""
    _log_header("Web UI Auto - 安装Playwright浏览器")

    cmd = [sys.executable, "-m", "playwright", "install"]
    if args.with_deps:
        cmd.append("--with-deps")

    logger.info(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    """主函数"""
    # 初始化 CLI 日志模式
    init_cli_logger()
    
    parser = argparse.ArgumentParser(
        prog="web-ui-auto",
        description="Web UI 自动化测试框架 - 命令行工具"
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行测试")
    run_parser.add_argument("test_path", nargs="?", default="tests/", help="测试路径")
    run_parser.add_argument("-m", "--markers", help="运行指定标记的测试")
    run_parser.add_argument("--html-report", action="store_true", help="生成HTML报告")
    run_parser.add_argument("--allure-dir", default="reports/allure-results", help="Allure报告目录")
    run_parser.set_defaults(func=cmd_run)

    # smoke 命令
    smoke_parser = subparsers.add_parser("smoke", help="运行冒烟测试")
    smoke_parser.add_argument("test_path", nargs="?", default="tests/", help="测试路径")
    smoke_parser.set_defaults(func=cmd_smoke)

    # critical 命令
    critical_parser = subparsers.add_parser("critical", help="运行关键路径测试")
    critical_parser.add_argument("test_path", nargs="?", default="tests/", help="测试路径")
    critical_parser.set_defaults(func=cmd_critical)

    # api 命令
    api_parser = subparsers.add_parser("api", help="运行API测试")
    api_parser.add_argument("test_path", nargs="?", default="tests/", help="测试路径")
    api_parser.set_defaults(func=cmd_api)

    # ui 命令
    ui_parser = subparsers.add_parser("ui", help="运行UI测试")
    ui_parser.add_argument("test_path", nargs="?", default="tests/", help="测试路径")
    ui_parser.set_defaults(func=cmd_ui)

    # report 命令
    report_parser = subparsers.add_parser("report", help="生成Allure报告")
    report_parser.add_argument("test_path", nargs="?", default="tests/", help="测试路径")
    report_parser.add_argument("--allure-dir", default="reports/allure-results", help="Allure报告目录")
    report_parser.set_defaults(func=cmd_report)

    # clean 命令
    clean_parser = subparsers.add_parser("clean", help="清理缓存和报告")
    clean_parser.set_defaults(func=cmd_clean)

    # install-browser 命令
    browser_parser = subparsers.add_parser("install-browser", help="安装Playwright浏览器")
    browser_parser.add_argument("--with-deps", action="store_true", help="同时安装系统依赖")
    browser_parser.set_defaults(func=cmd_install_browser)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
