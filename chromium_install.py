# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chromium 浏览器自动安装脚本
支持 Windows/Linux/macOS 多平台
支持多种架构: x86_64, arm64, aarch64
"""

import sys
import os
import re
import json
import time
import shutil
import zipfile
import subprocess
import platform as _platform
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

try:
    import requests
except ImportError:
    print("❌ 缺少依赖库 requests，请先安装: pip install requests")
    sys.exit(1)

# ============================================
# 全局配置
# ============================================

PROJECT_ROOT = Path(__file__).resolve().parent
CHROMIUM_DIR = PROJECT_ROOT / "chromium" / "chrome-win64"
TEMP_DIR = PROJECT_ROOT / ".temp_chromium_download"
ENV_FILE = PROJECT_ROOT / ".chromium_env"
RECORD_FILE = PROJECT_ROOT / "chromium_install_record.txt"

# Chrome for Testing API
CHROME_FOR_TESTING_API = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"

# 下载配置
DOWNLOAD_CONFIG = {
    "max_retries": 5,
    "retry_delay": 3,
    "timeout": 60,
    "chunk_size": 8192 * 16,
    "progress_interval": 0.5
}


# ============================================
# 日志工具类
# ============================================

class Logger:
    """跨平台彩色日志系统（Linux 兼容）"""

    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'bold': '\033[1m',
        'reset': '\033[0m'
    }

    @staticmethod
    def colorize(text: str, color: str) -> str:
        if not sys.stdout.isatty():
            return text
        return f"{Logger.COLORS.get(color, '')}{text}{Logger.COLORS['reset']}"

    @staticmethod
    def info(msg: str):
        print(f"  ℹ️  {msg}")

    @staticmethod
    def success(msg: str):
        print(f"  ✅ {Logger.colorize(msg, 'green')}")

    @staticmethod
    def warning(msg: str):
        print(f"  ⚠️  {Logger.colorize(msg, 'yellow')}")

    @staticmethod
    def error(msg: str):
        print(f"  ❌ {Logger.colorize(msg, 'red')}")

    @staticmethod
    def step(current: int, total: int, msg: str):
        prefix = Logger.colorize(f"[{current}/{total}]", 'cyan')
        print(f"\n{prefix} {Logger.colorize(msg, 'bold')}")


log = Logger()


# ============================================
# 环境检测模块
# ============================================

class EnvironmentChecker:
    """跨平台环境检测器"""

    @staticmethod
    def check_dependencies() -> bool:
        """检查必要的依赖"""
        try:
            import requests
            log.success("依赖检查通过")
            return True
        except ImportError as e:
            log.error(f"缺少依赖: {e}")
            log.info("请运行: pip install requests")
            return False

    @staticmethod
    def get_playwright_version() -> Optional[str]:
        """获取 Playwright 版本"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", "playwright"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        version = line.split(':')[1].strip()
                        log.success(f"Playwright 版本: {version}")
                        return version
            else:
                log.warning("未检测到 Playwright")
                return None

        except Exception as e:
            log.warning(f"检查 Playwright 版本失败: {e}")
            return None

    @staticmethod
    def get_chrome_version() -> Optional[Tuple[str, str]]:
        """
        获取系统 Chrome/Chromium 版本（跨平台支持）

        方法：
        Windows:
        1. PowerShell 读取文件属性（推荐，无需额外依赖）
        2. 注册表读取（备用）

        Linux:
        1. 命令行查询 (google-chrome, chromium, chromium-browser)
        2. 包管理器查询 (dpkg, rpm)

        macOS:
        1. 应用程序目录查询

        Returns:
            (完整版本号, 主版本号) 或 None
        """
        # ========== Windows 平台 ==========
        if sys.platform.startswith("win"):
            return EnvironmentChecker._get_chrome_version_windows()

        # ========== Linux 平台 ==========
        elif sys.platform.startswith("linux"):
            return EnvironmentChecker._get_chrome_version_linux()

        # ========== macOS 平台 ==========
        elif sys.platform.startswith("darwin"):
            return EnvironmentChecker._get_chrome_version_macos()

        return None

    @staticmethod
    def _get_chrome_version_windows() -> Optional[Tuple[str, str]]:
        """Windows 平台获取 Chrome 版本"""
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]

        for chrome_path in chrome_paths:
            if Path(chrome_path).exists():
                try:
                    # 方法1: 使用 PowerShell 读取文件属性（无需启动浏览器）
                    ps_command = f"""
                    $file = Get-Item '{chrome_path}'
                    $version = $file.VersionInfo.ProductVersion
                    Write-Output $version
                    """

                    result = subprocess.run(
                        ["powershell", "-Command", ps_command],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW  # 隐藏窗口
                    )

                    if result.returncode == 0:
                        version_str = result.stdout.strip()
                        match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version_str)
                        if match:
                            full_version = match.group(0)
                            major_version = match.group(1)
                            log.success(f"检测到 Chrome 版本: {full_version} (通过文件属性)")
                            return full_version, major_version

                except Exception as e:
                    log.warning(f"读取 Chrome 版本失败: {e}")

        # 方法2: 读取注册表（最后备选）
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Google\Chrome\BLBeacon"
            )
            version, _ = winreg.QueryValueEx(key, "version")
            winreg.CloseKey(key)

            major_version = version.split('.')[0]
            log.success(f"检测到 Chrome 版本: {version} (通过注册表)")
            return version, major_version

        except Exception:
            pass

        log.warning("未检测到 Google Chrome")
        return None

    @staticmethod
    def _get_chrome_version_linux() -> Optional[Tuple[str, str]]:
        """Linux 平台获取 Chrome/Chromium 版本"""
        # 常见的 Chrome/Chromium 命令
        chrome_commands = [
            "google-chrome",
            "google-chrome-stable",
            "chromium",
            "chromium-browser",
            "chromium-browser-stable",
        ]

        # 方法1: 通过命令行查询版本
        for cmd in chrome_commands:
            try:
                result = subprocess.run(
                    [cmd, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    env={**os.environ, "LANG": "C"}  # 统一语言环境
                )

                if result.returncode == 0:
                    version_output = result.stdout.strip()
                    # 解析版本字符串，如 "Google Chrome 148.0.7778.217" 或 "Chromium 148.0.7778.217"
                    match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version_output)
                    if match:
                        full_version = match.group(0)
                        major_version = match.group(1)
                        browser_name = version_output.split()[0] if version_output else "Chrome"
                        log.success(f"检测到 {browser_name} 版本: {full_version} (通过命令行)")
                        return full_version, major_version

            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        # 方法2: 通过包管理器查询（Debian/Ubuntu）
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f", "${Version}", "google-chrome-stable"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('-')[0]  # 移除包版本后缀
                match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version)
                if match:
                    full_version = match.group(0)
                    major_version = match.group(1)
                    log.success(f"检测到 Chrome 版本: {full_version} (通过 dpkg)")
                    return full_version, major_version
        except Exception:
            pass

        # 方法3: 通过包管理器查询（RPM-based: CentOS/RHEL/Fedora）
        try:
            result = subprocess.run(
                ["rpm", "-q", "--queryformat", "%{VERSION}", "google-chrome-stable"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and "not installed" not in result.stdout.lower():
                version = result.stdout.strip()
                match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version)
                if match:
                    full_version = match.group(0)
                    major_version = match.group(1)
                    log.success(f"检测到 Chrome 版本: {full_version} (通过 rpm)")
                    return full_version, major_version
        except Exception:
            pass

        # 方法4: 检查 Chromium 包
        try:
            result = subprocess.run(
                ["dpkg-query", "-W", "-f", "${Version}", "chromium-browser"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('-')[0]
                match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version)
                if match:
                    full_version = match.group(0)
                    major_version = match.group(1)
                    log.success(f"检测到 Chromium 版本: {full_version} (通过 dpkg)")
                    return full_version, major_version
        except Exception:
            pass

        log.warning("未检测到 Chrome/Chromium")
        return None

    @staticmethod
    def _get_chrome_version_macos() -> Optional[Tuple[str, str]]:
        """macOS 平台获取 Chrome 版本"""
        chrome_app_path = "/Applications/Google Chrome.app"

        if not Path(chrome_app_path).exists():
            log.warning("未检测到 Google Chrome")
            return None

        try:
            # 使用 defaults 命令读取 Info.plist
            result = subprocess.run(
                ["defaults", "read", f"{chrome_app_path}/Contents/Info", "CFBundleShortVersionString"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                match = re.search(r'(\d+)\.(\d+)\.(\d+)\.(\d+)', version)
                if match:
                    full_version = match.group(0)
                    major_version = match.group(1)
                    log.success(f"检测到 Chrome 版本: {full_version} (通过 macOS)")
                    return full_version, major_version
                else:
                    # 如果版本号格式不匹配，尝试直接使用
                    log.success(f"检测到 Chrome 版本: {version} (通过 macOS)")
                    return version, version.split('.')[0]

        except Exception as e:
            log.warning(f"读取 Chrome 版本失败: {e}")

        return None


# ============================================
# 版本匹配模块
# ============================================

class VersionMatcher:
    """智能版本匹配器"""

    @staticmethod
    def get_playwright_recommended_version() -> Optional[str]:
        """
        从 Playwright 获取推荐的 Chromium 版本

        方法：
        1. 通过 playwright install --dry-run 命令获取
        2. 解析 Playwright 包中的浏览器版本映射

        Returns:
            推荐的 Chromium 完整版本号，或 None
        """
        try:
            log.info("查询 Playwright 推荐的 Chromium 版本...")

            # 方法1: 通过 playwright 命令获取
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and result.stdout:
                # 解析输出，支持多种格式：
                # 格式1: "Chrome for Testing 148.0.7778.96 (playwright chromium v1223)"
                # 格式2: "Chromium 1208 (145.0.7632.6)"
                match = re.search(r'(?:Chrome for Testing|Chromium)\s+(?:v?\d+\s+)?([\d.]+)', result.stdout)
                if match:
                    version = match.group(1)
                    log.success(f"Playwright 推荐版本: {version} (通过 dry-run)")
                    return version
                else:
                    log.warning(f"dry-run 输出格式不符合预期: {result.stdout[:200]}")
            else:
                log.warning(
                    f"dry-run 命令执行失败: returncode={result.returncode}, stderr={result.stderr[:200] if result.stderr else 'None'}")

            # 方法2: 从 Playwright 包中读取版本映射文件
            try:
                import importlib.metadata

                # 获取 Playwright 安装路径
                dist = importlib.metadata.distribution('playwright')
                if hasattr(dist, '_path'):
                    package_path = Path(str(dist._path))

                    # 尝试多个可能的路径
                    possible_paths = [
                        package_path.parent / "playwright" / "driver" / "package" / "browsers.json",
                        package_path / "playwright" / "driver" / "package" / "browsers.json",
                    ]

                    for browsers_json in possible_paths:
                        if browsers_json.exists():
                            with open(browsers_json, 'r', encoding='utf-8') as f:
                                data = json.load(f)

                                # 情况1: 字典结构 {"browsers": {"chromium": {...}}}
                                if isinstance(data, dict):
                                    browsers = data.get('browsers')

                                    # 检查 browsers 是否为字典
                                    if isinstance(browsers, dict):
                                        chromium_info = browsers.get('chromium')

                                        # 如果 chromium 是字典，提取 revision
                                        if isinstance(chromium_info, dict):
                                            revision = chromium_info.get('revision')
                                            if revision:
                                                log.success(
                                                    f"Playwright 推荐版本: {revision} (通过 browsers.json 字典结构)")
                                                return revision

                                        # 如果 chromium 是列表（兼容特殊情况）
                                        elif isinstance(chromium_info, list):
                                            for item in chromium_info:
                                                if isinstance(item, dict) and item.get('name') == 'chromium':
                                                    revision = item.get('revision')
                                                    if revision:
                                                        log.success(
                                                            f"Playwright 推荐版本: {revision} (通过 browsers.json 嵌套列表)")
                                                        return revision

                                    # 如果 browsers 字段不存在或不是字典，尝试直接从根节点查找
                                    elif browsers is None:
                                        log.warning("browsers 字段不存在，尝试其他解析方式")

                                # 情况2: 数组结构 [{"name": "chromium", "revision": "xxx"}, ...]
                                elif isinstance(data, list):
                                    for item in data:
                                        if isinstance(item, dict):
                                            # 检查是否有 name 字段且为 chromium
                                            if item.get('name') == 'chromium':
                                                revision = item.get('revision')
                                                if revision:
                                                    log.success(
                                                        f"Playwright 推荐版本: {revision} (通过 browsers.json 数组结构)")
                                                    return revision
                                            # 或者检查是否有 browser 字段
                                            elif item.get('browser') == 'chromium':
                                                revision = item.get('revision') or item.get('version')
                                                if revision:
                                                    log.success(
                                                        f"Playwright 推荐版本: {revision} (通过 browsers.json 数组结构 browser 字段)")
                                                    return revision

                                else:
                                    log.warning(f"JSON 数据格式未知: {type(data)}")

            except Exception as e:
                log.warning(f"从 Playwright 包读取版本失败: {e}")

            log.warning("无法从 Playwright 获取推荐版本")
            return None

        except Exception as e:
            log.warning(f"查询 Playwright 推荐版本失败: {e}")
            return None

    @staticmethod
    def fetch_available_versions() -> Optional[List[Dict]]:
        """获取可用的 Chromium 版本列表"""
        try:
            log.info("查询 Chromium 版本列表...")
            response = requests.get(CHROME_FOR_TESTING_API, timeout=30)
            response.raise_for_status()
            data = response.json()
            versions = data.get("versions", [])
            log.success(f"获取到 {len(versions)} 个可用版本")
            return versions
        except Exception as e:
            log.error(f"查询版本列表失败: {e}")
            return None

    @staticmethod
    def match_by_chrome_version(chrome_major: str, versions: List[Dict]) -> Optional[Dict]:
        """
        根据 Chrome 主版本号匹配 Chromium 版本（遵循 Playwright 官方规则）

        Playwright 官方版本匹配规则：
        - Playwright 的 Chromium 版本总是比 Chrome 稳定版超前 1 个主版本（N+1）
        - 例如：Chrome 148 → Playwright 使用 Chromium 149

        策略优先级：
        1. Chromium N+1（Playwright 官方超前策略，最高优先级）
        2. 精确匹配主版本（兼容特殊情况）
        3. 相邻版本 ±1（容错策略）
        4. 最新版本（兜底策略）

        Args:
            chrome_major: Chrome 主版本号（字符串）
            versions: 可用版本列表

        Returns:
            匹配的版本信息字典，或 None
        """
        log.info(f"根据 Chrome 主版本 {chrome_major} 匹配 Chromium...")

        chrome_major_int = int(chrome_major)

        # ========== 策略1: Chromium N+1（Playwright 官方超前策略）==========
        # 这是 Playwright 的默认行为：Chromium 领先 Chrome 稳定版 1 个主版本
        n_plus_1 = str(chrome_major_int + 1)
        for version_info in versions:
            # 增加类型检查
            if not isinstance(version_info, dict) or "version" not in version_info:
                continue
            version_major = version_info["version"].split(".")[0]
            if version_major == n_plus_1:
                log.success(
                    f"✓ 使用 Chromium N+1 策略: {version_info['version']} (Chrome {chrome_major} → Chromium {n_plus_1})")
                return version_info

        log.warning(f"未找到 N+1 版本 ({n_plus_1})，尝试其他策略...")

        # ========== 策略2: 精确匹配主版本（特殊情况兼容）==========
        exact_matches = []
        for version_info in versions:
            # 增加类型检查
            if not isinstance(version_info, dict) or "version" not in version_info:
                continue
            version = version_info["version"]
            version_major = version.split(".")[0]
            if version_major == chrome_major:
                exact_matches.append(version_info)

        if exact_matches:
            best_match = exact_matches[-1]  # 选择最新的修订版本
            log.success(f"✓ 精确匹配: {best_match['version']}")
            return best_match

        log.warning(f"未找到主版本 {chrome_major} 的精确匹配")

        # ========== 策略3: 相邻版本 ±1（容错策略）==========
        # 先尝试 N-1，再尝试 N+2
        for offset in [-1, 2]:
            adjacent = str(chrome_major_int + offset)
            for version_info in versions:
                # 增加类型检查
                if not isinstance(version_info, dict) or "version" not in version_info:
                    continue
                version_major = version_info["version"].split(".")[0]
                if version_major == adjacent:
                    log.info(f"✓ 使用相邻版本: {version_info['version']} (偏移: {offset})")
                    return version_info

        # ========== 策略4: 最新版本（兜底策略）==========
        if versions:
            latest = versions[-1]
            # 增加类型检查
            if isinstance(latest, dict) and "version" in latest:
                log.warning(f"⚠ 使用最新版本作为兜底: {latest['version']}")
                return latest

        log.error("❌ 未找到任何可用的 Chromium 版本")
        return None

    @staticmethod
    def get_download_url(version_info: Dict, platform: str = "win64") -> Optional[Tuple[str, str]]:
        """获取指定平台的下载链接"""
        downloads = version_info.get("downloads", {})
        chrome_downloads = downloads.get("chrome", [])

        for download in chrome_downloads:
            if download.get("platform") == platform:
                return download["url"], version_info["version"]

        log.error(f"未找到 {platform} 平台的下载链接")
        return None

    @staticmethod
    def build_download_url(chrome_version: str, platform: str = "win64") -> str:
        """
        根据 Chrome 版本构建官方下载链接

        Chrome for Testing 官方格式：
        https://storage.googleapis.com/chrome-for-testing-public/{version}/{platform}/chrome-{platform}.zip
        """
        return f"https://storage.googleapis.com/chrome-for-testing-public/{chrome_version}/{platform}/chrome-{platform}.zip"

    @staticmethod
    def build_download_urls(version: str, platform: str = "win64") -> List[Tuple[str, str]]:
        """
        按优先级生成下载链接列表：Google 官方

        Returns:
            List of (name, url) tuples
        """
        suffix = f"/{version}/{platform}/chrome-{platform}.zip"
        urls = [("Google", f"https://storage.googleapis.com/chrome-for-testing-public{suffix}")]
        return urls

    @staticmethod
    def get_platform() -> str:
        """获取当前平台（支持 Windows/Linux/macOS 及多种架构）"""
        import platform as _platform

        if sys.platform.startswith("win"):
            # Windows: 检测架构
            arch = _platform.machine().lower()
            if arch in ("arm64", "aarch64"):
                return "win-arm64"
            else:
                return "win64"

        elif sys.platform.startswith("darwin"):
            # macOS: 检测架构
            arch = _platform.machine()
            if arch in ("arm64", "aarch64"):
                return "mac-arm64"
            else:
                return "mac-x64"

        elif sys.platform.startswith("linux"):
            # Linux: 检测架构
            arch = _platform.machine().lower()
            if arch in ("arm64", "aarch64"):
                return "linux-arm64"
            elif arch in ("x86_64", "amd64"):
                return "linux"
            else:
                raise Exception(f"不支持的 Linux 架构: {arch}")

        else:
            raise Exception(f"不支持的平台: {sys.platform}")


# ============================================
# 高可靠下载模块
# ============================================

class ReliableDownloader:
    """高可靠下载器"""

    def __init__(self, config: Dict = None):
        self.config = config or DOWNLOAD_CONFIG
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def download(self, url: str, dest_path: Path) -> bool:
        """带容错机制的文件下载"""
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        for attempt in range(1, self.config["max_retries"] + 1):
            try:
                log.info(f"开始下载 (尝试 {attempt}/{self.config['max_retries']})")
                log.info(f"目标地址: {url}")

                resume_pos = 0
                if dest_path.exists():
                    resume_pos = dest_path.stat().st_size
                    log.info(f"检测到部分文件，从 {resume_pos / 1024 / 1024:.2f} MB 处继续")

                headers = {}
                if resume_pos > 0:
                    headers["Range"] = f"bytes={resume_pos}-"

                response = self.session.get(
                    url,
                    headers=headers,
                    stream=True,
                    timeout=self.config["timeout"]
                )
                response.raise_for_status()

                total_size = int(response.headers.get("Content-Length", 0))
                if resume_pos > 0:
                    total_size += resume_pos

                mode = "ab" if resume_pos > 0 else "wb"
                downloaded = resume_pos
                last_update = 0

                with open(dest_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=self.config["chunk_size"]):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

                            current_time = time.time()
                            if current_time - last_update >= self.config["progress_interval"]:
                                if total_size > 0:
                                    percent = (downloaded / total_size) * 100
                                    downloaded_mb = downloaded / (1024 * 1024)
                                    total_mb = total_size / (1024 * 1024)
                                    print(f"\r  进度: {percent:5.1f}% | {downloaded_mb:6.2f} MB / {total_mb:6.2f} MB",
                                          end="", flush=True)
                                else:
                                    downloaded_mb = downloaded / (1024 * 1024)
                                    print(f"\r  已下载: {downloaded_mb:.2f} MB", end="", flush=True)
                                last_update = current_time

                print()
                file_size_mb = dest_path.stat().st_size / (1024 * 1024)
                log.success(f"下载完成: {dest_path.name} ({file_size_mb:.2f} MB)")
                return True

            except requests.exceptions.Timeout:
                log.warning(f"下载超时 (尝试 {attempt}/{self.config['max_retries']})")
            except requests.exceptions.ConnectionError:
                log.warning(f"连接失败 (尝试 {attempt}/{self.config['max_retries']})")
            except requests.exceptions.RequestException as e:
                log.warning(f"下载异常: {e} (尝试 {attempt}/{self.config['max_retries']})")

            if attempt < self.config["max_retries"]:
                log.info(f"等待 {self.config['retry_delay']} 秒后重试...")
                time.sleep(self.config["retry_delay"])

        log.error(f"下载失败，已达到最大重试次数 ({self.config['max_retries']})")
        return False


# ============================================
# 文件验证模块
# ============================================

class FileValidator:
    """文件验证器"""

    @staticmethod
    def check_zip(zip_path: Path) -> bool:
        """校验 ZIP 文件完整性"""
        if not zip_path.exists():
            log.error(f"文件不存在: {zip_path}")
            return False

        file_size = zip_path.stat().st_size
        if file_size < 1024 * 1024:  # 小于 1MB
            log.error(f"文件大小异常: {file_size / 1024:.2f} KB")
            return False

        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                bad_file = zf.testzip()
                if bad_file:
                    log.error(f"ZIP 文件损坏: {bad_file}")
                    return False
        except zipfile.BadZipFile:
            log.error("无效的 ZIP 文件")
            return False

        file_size_mb = file_size / (1024 * 1024)
        log.success(f"文件校验通过: {zip_path.name} ({file_size_mb:.2f} MB)")
        return True


# ============================================
# 主安装流程
# ============================================

class ChromiumInstaller:
    """Chromium 安装管理器"""

    def __init__(self, source_type: str = "auto", local_path: Optional[str] = None,
                 url: Optional[str] = None, version: Optional[str] = None):
        """
        初始化安装器

        Args:
            source_type: 来源类型 (auto/local/url)
            local_path: 本地 ZIP 文件路径
            url: 自定义下载 URL
            version: 指定 Chromium 版本
        """
        self.source_type = source_type
        self.local_path = Path(local_path) if local_path else None
        self.custom_url = url
        self.specified_version = version

        self.zip_path = TEMP_DIR / "chromium.zip"
        self.chromium_version = "unknown"
        self.download_url = ""
        self.download_urls = []
        self.match_strategy = "Unknown"

        self.downloader = ReliableDownloader()
        self.validator = FileValidator()

    def _detect_chromium_version(self) -> Tuple[Optional[str], Optional[str]]:
        """
        统一的版本检测逻辑
        
        检测优先级：
        1. 从 Playwright 获取推荐版本
        2. 根据系统 Chrome 版本匹配
        3. 使用最新版本兜底
        
        Returns:
            (推荐的版本号, 匹配策略说明) 或 (None, None)
        """
        log.step(0, 1, "版本检测分析")

        # 获取系统 Chrome 版本
        chrome_version = EnvironmentChecker.get_chrome_version()

        # 优先尝试从 Playwright 获取推荐版本
        playwright_recommended = VersionMatcher.get_playwright_recommended_version()

        # 获取在线版本列表
        versions = VersionMatcher.fetch_available_versions()

        # ========== 在线模式 ==========
        if versions:
            log.info("Google API 可用，使用在线匹配模式")
            matched = None

            # 策略1: 优先使用 Playwright 推荐的版本
            if playwright_recommended:
                for version_info in versions:
                    if not isinstance(version_info, dict):
                        continue
                    if version_info.get("version") == playwright_recommended:
                        matched = version_info
                        strategy = f"Playwright 推荐 ({playwright_recommended})"
                        log.success(f"✓ 找到 Playwright 推荐版本: {playwright_recommended}")
                        return playwright_recommended, strategy

            # 策略2: 根据 Chrome 版本匹配（N+1 策略）
            if chrome_version:
                _, major = chrome_version
                matched = VersionMatcher.match_by_chrome_version(major, versions)
                if matched:
                    version = matched.get("version")
                    strategy = f"Chrome {major} (N+1 策略)"
                    return version, strategy

            # 策略3: 使用最新版本兜底
            if versions and isinstance(versions[-1], dict):
                latest = versions[-1]
                version = latest.get("version")
                log.warning(f"⚠ 使用最新版本作为兜底: {version}")
                return version, "Latest"

            log.error("未找到匹配的 Chromium 版本")
            return None, None

        # ========== 离线模式 ==========
        else:
            log.warning("Google API 不可用，使用离线降级策略")

            # 策略1: 使用 Playwright 推荐版本
            if playwright_recommended:
                log.success(f"使用 Playwright 推荐版本: {playwright_recommended}")
                return playwright_recommended, "Playwright 推荐 (离线模式)"

            # 策略2: 直接使用 Chrome 版本号
            elif chrome_version:
                full_ver, major_ver = chrome_version
                log.warning(f"⚠ 使用 Chrome 版本直接匹配: {full_ver}")
                return full_ver, f"Chrome {major_ver} 直接匹配 (离线)"

            else:
                log.error("❌ 未检测到 Chrome 版本，且 API 不可用，无法匹配")
                return None, None

    def _match_version(self) -> bool:
        """自动匹配 Chromium 版本（遵循 Playwright 官方规则）"""
        # 调用统一的版本检测方法
        version, strategy = self._detect_chromium_version()

        if not version:
            log.error("版本匹配失败")
            return False

        self.chromium_version = version
        self.match_strategy = strategy

        # 生成下载链接列表
        self.download_urls = VersionMatcher.build_download_urls(self.chromium_version, VersionMatcher.get_platform())
        self.download_url = self.download_urls[0][1]

        log.success(f"确定下载版本: {self.chromium_version}")
        log.info(f"匹配策略: {self.match_strategy}")
        log.info(f"下载源: {self.download_urls[0][0]}")

        return True

    def install(self) -> bool:
        """执行完整安装流程"""
        try:
            # 确保项目根目录存在
            PROJECT_ROOT.mkdir(parents=True, exist_ok=True)

            # 步骤1: 清理并重建临时目录
            log.step(1, 4, "清理临时文件")
            self._cleanup_temp()

            # 确保临时目录存在（关键：清理后必须重建）
            TEMP_DIR.mkdir(parents=True, exist_ok=True)

            # 步骤2: 下载或复制文件
            log.step(2, 4, "准备安装包")
            if self.source_type == "local":
                # 本地文件模式：检查用户提供的文件
                if not self.local_path or not self.local_path.exists():
                    log.error(f"本地文件不存在: {self.local_path}")
                    return False

                # 复制到临时目录
                log.info(f"复制本地文件: {self.local_path.name} → {self.zip_path.name}")
                shutil.copy2(str(self.local_path), str(self.zip_path))

                # 校验文件
                if not self.validator.check_zip(self.zip_path):
                    return False
            else:
                # 在线下载模式：确保临时目录存在
                TEMP_DIR.mkdir(parents=True, exist_ok=True)

                # 构建待尝试的 URL 列表
                urls_to_try = []
                if self.source_type == "url" and not self.download_urls:
                    urls_to_try = [("指定 URL", self.download_url)]
                elif self.download_urls:
                    urls_to_try = self.download_urls
                else:
                    urls_to_try = [("下载地址", self.download_url)]

                # 先 HEAD 嗅探，找到第一个可达的地址
                log.info("正在探测可用镜像...")
                target_url = None
                target_name = None
                for name, url in urls_to_try:
                    try:
                        resp = requests.head(url, timeout=10)
                        if resp.status_code == 200:
                            target_url = url
                            target_name = name
                            log.success(f"[{name}] 可用: {url}")
                            break
                        else:
                            log.warning(f"[{name}] 返回 {resp.status_code}，尝试下一个...")
                    except Exception as e:
                        log.warning(f"[{name}] 不可达 ({e})，尝试下一个...")

                if not target_url:
                    log.error("所有镜像均不可达")
                    return False

                # 开始下载（downloader 内部会确保目录存在）
                if not self.downloader.download(target_url, self.zip_path):
                    return False

                if not self.validator.check_zip(self.zip_path):
                    return False

            # 步骤3: 解压
            log.step(3, 4, "解压安装包")
            if not self._extract_and_setup():
                return False

            # 步骤4: 生成配置
            log.step(4, 4, "生成配置文件")
            self._generate_record()

            log.success("Chromium 安装完成！")
            return True

        except Exception as e:
            log.error(f"安装失败: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 清理临时文件（保留下载的文件）
            if self.source_type != "local" and TEMP_DIR.exists():
                try:
                    shutil.rmtree(TEMP_DIR, ignore_errors=True)
                except Exception as e:
                    log.warning(f"清理临时目录失败: {e}")

    def _cleanup_temp(self):
        """清理临时文件"""
        if TEMP_DIR.exists():
            try:
                shutil.rmtree(TEMP_DIR, ignore_errors=True)
                log.info("临时目录已清理")
            except Exception as e:
                log.warning(f"清理临时目录失败: {e}")

        # 确保临时目录存在且为空
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

    def _extract_and_setup(self) -> bool:
        """解压并生成标准目录结构"""
        try:
            # 步骤1: 清理旧版本
            if CHROMIUM_DIR.exists():
                log.info("清理旧版本 Chromium")
                shutil.rmtree(CHROMIUM_DIR, ignore_errors=True)

            # 步骤2: 确保父目录存在
            CHROMIUM_DIR.parent.mkdir(parents=True, exist_ok=True)

            # 步骤3: 准备临时解压目录
            temp_extract = TEMP_DIR / "extract_temp"
            if temp_extract.exists():
                shutil.rmtree(temp_extract, ignore_errors=True)
            temp_extract.mkdir(parents=True, exist_ok=True)

            # 步骤4: 解压到临时目录
            log.info(f"解压到临时目录: {temp_extract}")
            with zipfile.ZipFile(self.zip_path, 'r') as zf:
                zf.extractall(temp_extract)

            # 步骤5: 检查解压后的目录结构
            extracted_items = list(temp_extract.iterdir())

            if not extracted_items:
                log.error("解压后目录为空")
                return False

            # 步骤6: 处理嵌套目录结构
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                inner_dir = extracted_items[0]
                if inner_dir.name in ["chrome-win64", "chrome-linux", "chrome-mac"]:
                    log.info(f"检测到嵌套目录结构: {inner_dir.name}")

                    # 创建目标目录（关键：必须先创建）
                    CHROMIUM_DIR.mkdir(parents=True, exist_ok=True)

                    # 移动内容到 CHROMIUM_DIR
                    log.info(f"移动内容到: {CHROMIUM_DIR}")
                    for item in inner_dir.iterdir():
                        dest_path = CHROMIUM_DIR / item.name
                        try:
                            if item.is_dir():
                                shutil.copytree(str(item), str(dest_path))
                                shutil.rmtree(item, ignore_errors=True)
                            else:
                                shutil.move(str(item), str(dest_path))
                        except Exception as e:
                            log.error(f"移动文件失败 {item.name}: {e}")
                            return False
                else:
                    # 直接移动整个目录
                    shutil.move(str(inner_dir), str(CHROMIUM_DIR))
            else:
                # 没有嵌套，创建目录后移动所有内容
                CHROMIUM_DIR.mkdir(parents=True, exist_ok=True)
                for item in extracted_items:
                    dest_path = CHROMIUM_DIR / item.name
                    try:
                        if item.is_dir():
                            shutil.copytree(str(item), str(dest_path))
                            shutil.rmtree(item, ignore_errors=True)
                        else:
                            shutil.move(str(item), str(dest_path))
                    except Exception as e:
                        log.error(f"移动文件失败 {item.name}: {e}")
                        return False

            # 步骤7: 清理临时解压目录
            shutil.rmtree(temp_extract, ignore_errors=True)

            # 步骤8: Linux/macOS 设置可执行权限
            if not sys.platform.startswith("win"):
                self._set_executable_permissions(CHROMIUM_DIR)

            # 步骤9: 验证安装
            chrome_exe = self._find_chrome_exe(CHROMIUM_DIR)
            if not chrome_exe:
                log.error("解压后未找到 chrome 可执行文件")
                log.error(f"检查目录: {CHROMIUM_DIR}")
                if CHROMIUM_DIR.exists():
                    contents = list(CHROMIUM_DIR.iterdir())
                    log.error(f"目录内容: {[str(c) for c in contents[:10]]}")
                return False

            relative_path = chrome_exe.relative_to(PROJECT_ROOT)
            log.success(f"解压完成，找到: {relative_path}")
            return True

        except PermissionError as e:
            log.error(f"权限不足: {e}")
            log.info("Linux 用户请尝试: sudo chmod +x 或重新运行")
            return False
        except zipfile.BadZipFile:
            log.error("ZIP 文件损坏，请重新下载")
            return False
        except Exception as e:
            log.error(f"解压失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _set_executable_permissions(self, base_dir: Path):
        """设置可执行权限（Linux/macOS）"""
        try:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    file_path = Path(root) / file
                    if file.endswith(('.sh', '.py')) or file.startswith('chrome'):
                        file_path.chmod(file_path.stat().st_mode | 0o755)
            log.success("已设置可执行权限")
        except Exception as e:
            log.warning(f"设置权限失败: {e}")

    def _find_chrome_exe(self, base_dir: Path) -> Optional[Path]:
        """查找 chrome 可执行文件"""
        if sys.platform.startswith("win"):
            patterns = ["chrome.exe", "*/chrome.exe", "*/*/chrome.exe"]
        else:
            patterns = ["chrome", "*/chrome", "*/*/chrome"]

        for pattern in patterns:
            matches = list(base_dir.glob(pattern))
            if matches:
                return matches[0]

        return None

    def _generate_record(self):
        """生成安装记录和环境变量文件"""
        # 查找 chrome 可执行文件
        chrome_exe = self._find_chrome_exe(CHROMIUM_DIR)
        executable_path = str(chrome_exe) if chrome_exe else ""

        # 如果版本是 unknown，尝试从可执行文件获取实际版本
        if self.chromium_version == "unknown" and chrome_exe and chrome_exe.exists():
            try:
                if sys.platform.startswith("win"):
                    ps_command = f"""
                            $file = Get-Item '{chrome_exe}'
                            $version = $file.VersionInfo.ProductVersion
                            Write-Output $version
                            """
                    result = subprocess.run(
                        ["powershell", "-Command", ps_command],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if result.returncode == 0:
                        version_str = result.stdout.strip()
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version_str)
                        if match:
                            self.chromium_version = match.group(1)
                            log.info(f"从可执行文件检测到版本: {self.chromium_version}")
                else:
                    result = subprocess.run(
                        [str(chrome_exe), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        version_str = result.stdout.strip()
                        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version_str)
                        if match:
                            self.chromium_version = match.group(1)
                            log.info(f"从可执行文件检测到版本: {self.chromium_version}")
            except Exception as e:
                log.warning(f"无法从可执行文件获取版本: {e}")

        record_content = f"""# Chromium 安装记录
        # 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

        安装版本: {self.chromium_version}
        安装时间: {time.strftime('%Y-%m-%d %H:%M:%S')}
        平台: {sys.platform}
        Python: {sys.version}
        匹配策略: {self.match_strategy}
        下载源: {self.download_urls[0][0] if self.download_urls else 'N/A'}
        """

        RECORD_FILE.write_text(record_content, encoding='utf-8')

        env_content = f"""# Chromium 环境变量配置
        # 自动生成于 {time.strftime('%Y-%m-%d %H:%M:%S')}
        # 启用自定义 Chromium（让 Playwright 使用项目中的浏览器）
        USE_CUSTOM_CHROMIUM=true

        # Chromium 可执行文件完整路径
        CHROMIUM_EXECUTABLE={executable_path}

        # Chromium 安装目录
        CHROMIUM_PATH={CHROMIUM_DIR}
        CHROMIUM_VERSION={self.chromium_version}
        CHROMIUM_PLATFORM={VersionMatcher.get_platform()}
        """

        ENV_FILE.write_text(env_content, encoding='utf-8')

        log.success(f"安装记录已保存: {RECORD_FILE.relative_to(PROJECT_ROOT)}")
        log.success(f"环境变量已保存: {ENV_FILE.relative_to(PROJECT_ROOT)}")

        if chrome_exe:
            log.success(f"可执行文件: {chrome_exe.relative_to(PROJECT_ROOT)}")
        else:
            log.warning("未找到 Chrome 可执行文件，请手动检查安装")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Chromium 浏览器自动安装工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
版本匹配策略（自动模式）:
  1. 优先从 Playwright 获取推荐的 Chromium 版本
  2. 若获取失败，则根据系统 Chrome 版本使用 N+1 策略匹配
  3. 最后使用最新可用版本作为兜底

示例:
  # 自动检测并安装（默认模式，推荐）
  python chromium_install.py
  python chromium_install.py --auto
  
  # 检测需要匹配的版本和下载地址
  python chromium_install.py --check
  
  # 使用本地 ZIP 文件安装
  python chromium_install.py --local /path/to/chrome-win64.zip
  
  # 从指定 URL 下载
  python chromium_install.py --url https://example.com/chrome-win64.zip
  
  # 卸载 Chromium
  python chromium_install.py --uninstall
  python chromium_install.py --uninstall -y  （静默卸载）

        """
    )

    parser.add_argument(
        "--local", "-l",
        type=str,
        help="本地 Chromium ZIP 文件路径（使用离线安装包）"
    )

    parser.add_argument(
        "--url", "-u",
        type=str,
        help="自定义下载 URL（从指定地址下载）"
    )

    parser.add_argument(
        "--auto", "-a",
        action="store_true",
        help="自动模式：检测系统 Chrome 版本并自动匹配下载 Chromium（默认选项）"
    )

    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="卸载已安装的 Chromium（清理安装目录和配置文件）"
    )

    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="静默模式：卸载时不需要确认（配合 --uninstall 使用）"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="检查版本匹配（仅显示匹配结果，不安装）"
    )

    args = parser.parse_args()

    # 检查版本模式（检测需要匹配的版本和下载地址）
    if args.check:
        print("\n" + "=" * 60)
        print("  Chromium 版本匹配检测工具")
        print("=" * 60)

        # 执行版本匹配逻辑
        chrome_version = EnvironmentChecker.get_chrome_version()
        playwright_recommended = VersionMatcher.get_playwright_recommended_version()
        versions = VersionMatcher.fetch_available_versions()

        print(f"\n📊 当前环境:")
        print(f"  操作系统: {sys.platform} ({_platform.machine()})")
        print(f"  Python: {sys.version.split()[0]}")
        print(f"  Playwright: {EnvironmentChecker.get_playwright_version() or '未安装'}")
        if chrome_version:
            print(f"  Chrome: {chrome_version[0]} (主版本: {chrome_version[1]})")
        else:
            print(f"  Chrome: 未检测到")

        print(f"\n🔍 版本检测结果:")

        if playwright_recommended:
            print(f"  ✅ Playwright 推荐版本: {playwright_recommended}")
        else:
            print(f"  ⚠️  Playwright 推荐版本: 无法获取")

        if not versions:
            log.error("无法获取在线版本列表，请检查网络连接")
            return

        # 模拟版本匹配逻辑
        matched_version = None
        match_strategy = None

        # 策略1: Playwright 推荐
        if playwright_recommended:
            for version_info in versions:
                if isinstance(version_info, dict) and version_info.get("version") == playwright_recommended:
                    matched_version = playwright_recommended
                    match_strategy = f"Playwright 推荐"
                    break

        # 策略2: Chrome N+1
        if not matched_version and chrome_version:
            _, major = chrome_version
            n_plus_1 = str(int(major) + 1)
            for version_info in versions:
                if isinstance(version_info, dict):
                    ver_major = version_info.get("version", "").split(".")[0]
                    if ver_major == n_plus_1:
                        matched_version = version_info.get("version")
                        match_strategy = f"Chrome {major} → Chromium {n_plus_1} (N+1 策略)"
                        break

        # 策略3: 最新版本
        if not matched_version and versions:
            latest = versions[-1]
            if isinstance(latest, dict) and "version" in latest:
                matched_version = latest["version"]
                match_strategy = "Latest (兜底策略)"

        if not matched_version:
            log.error("未找到匹配的 Chromium 版本")
            return

        print(f"  ✅ 匹配版本: {matched_version}")
        print(f"  📝 匹配策略: {match_strategy}")

        # 生成下载链接
        platform = VersionMatcher.get_platform()
        download_urls = VersionMatcher.build_download_urls(matched_version, platform)

        print(f"\n⬇️  下载地址:")
        for name, url in download_urls:
            print(f"  [{name}]")
            print(f"  {url}")

        print(f"\n💡 安装命令:")
        print(f"  # 方式1: 自动安装（使用匹配的版本）")
        print(f"  python chromium_install.py --auto")
        print(f"\n  # 方式2: 指定 URL 安装")
        print(f"  python chromium_install.py --url \"{download_urls[0][1]}\"")

        print("\n" + "=" * 60)
        return

    # 卸载模式
    if args.uninstall:
        print("\n" + "=" * 60)
        print("  Chromium 卸载工具")
        print("=" * 60)

        # 如果没有 -y 参数，提示用户确认
        if not args.yes:
            print(f"\n⚠️  即将卸载 Chromium，将删除以下内容:")
            print(f"  - 安装目录: {CHROMIUM_DIR}")
            print(f"  - 配置文件: {ENV_FILE.name}, {RECORD_FILE.name}")
            print(f"  - 临时文件: {TEMP_DIR}")

            confirm = input("\n是否继续? [y/N]: ").strip().lower()
            if confirm not in ['y', 'yes']:
                log.info("操作已取消")
                return
            print()

        if CHROMIUM_DIR.exists():
            log.info(f"正在卸载 Chromium: {CHROMIUM_DIR}")
            try:
                shutil.rmtree(CHROMIUM_DIR, ignore_errors=True)
                log.success("Chromium 目录已删除")
            except Exception as e:
                log.error(f"删除 Chromium 目录失败: {e}")
        else:
            log.warning("Chromium 目录不存在，无需卸载")

        # 清理配置文件
        for config_file in [ENV_FILE, RECORD_FILE]:
            if config_file.exists():
                try:
                    config_file.unlink()
                    log.success(f"配置文件已删除: {config_file.name}")
                except Exception as e:
                    log.warning(f"删除配置文件失败: {e}")

        # 清理临时目录
        if TEMP_DIR.exists():
            try:
                shutil.rmtree(TEMP_DIR, ignore_errors=True)
                log.success("临时目录已清理")
            except Exception as e:
                log.warning(f"清理临时目录失败: {e}")

        print("\n" + "=" * 60)
        print("  ✅ 卸载完成！")
        print("=" * 60)
        return

    # 安装模式
    print("\n" + "=" * 60)
    print("  Chromium 自动安装工具")
    print("=" * 60)

    # 检查依赖
    if not EnvironmentChecker.check_dependencies():
        sys.exit(1)

    # 显示环境信息
    playwright_version = EnvironmentChecker.get_playwright_version()
    chrome_version = EnvironmentChecker.get_chrome_version()

    print(f"\n📊 当前环境:")
    print(f"  操作系统: {sys.platform} ({_platform.machine()})")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Playwright: {playwright_version or '未安装'}")
    if chrome_version:
        print(f"  Chrome: {chrome_version[0]}")
    else:
        print(f"  Chrome: 未检测到")

    # 根据参数创建安装器
    if args.local:
        source_type = "local"
        local_path = args.local
        log.info(f"使用本地文件: {local_path}")

        installer = ChromiumInstaller(
            source_type=source_type,
            local_path=local_path,
            url=None
        )

        # 本地文件模式：跳过版本匹配，直接安装
        log.info("本地文件模式：跳过版本匹配")
    elif args.url:
        source_type = "url"
        local_path = None
        log.info(f"使用自定义 URL: {args.url}")

        installer = ChromiumInstaller(
            source_type=source_type,
            local_path=None,
            url=args.url
        )

        # URL 模式：需要版本匹配
        if not installer._match_version():
            log.error("版本匹配失败")
            sys.exit(1)
    else:
        # 默认 auto 模式：自动检测系统 Chrome 版本，匹配对应的 Chromium 并下载
        source_type = "auto"
        local_path = None
        if args.auto:
            log.info("自动模式：将检测系统 Chrome 版本并自动匹配下载 Chromium")
        else:
            log.info("默认自动模式：将检测系统 Chrome 版本并自动匹配下载 Chromium")

        installer = ChromiumInstaller(
            source_type=source_type,
            local_path=None,
            url=None
        )

        # 执行版本匹配（auto 模式会根据系统 Chrome 自动匹配）
        if not installer._match_version():
            log.error("版本匹配失败")
            sys.exit(1)

    # 执行安装
    if not installer.install():
        log.error("安装失败")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  ✅ 安装成功！")
    print("=" * 60)
    print(f"\n📦 Chromium 已安装到: {CHROMIUM_DIR}")
    print(f"🔧 版本: {installer.chromium_version}")
    print(f"📝 策略: {installer.match_strategy}")
    print(f"\n💡 提示: 可以运行以下命令测试:")
    print(f"   playwright test --headed")


if __name__ == "__main__":
    main()
