# web_ui_auto web前端UI自动化测试框架

> 基于 Playwright + Pytest 的企业级自动化测试框架

## 项目说明

本项目是一个完整的 UI 自动化测试框架，采用 POM（Page Object Model）设计模式。

### 核心特性

- ✅ **POM 模式**：页面对象模型，提高代码可维护性
- ✅ **配置分离**：多环境配置管理（dev/qa/prod）
- ✅ **工具封装**：日志、截图、录屏等通用工具
- ✅ **src-layout**：源码隔离，符合企业标准布局
- ✅ **自动报告**：Allure 测试报告集成
- ✅ **失败追踪**：自动截图和录像保留现场

## 目录结构说明

```
web_ui_auto/                     # 项目根目录（全小写、短名）
├── .gitignore                 # 忽略：logs、reports、videos、.env、venv
├── README.md                  # 项目说明、部署、运行命令
├── setup.py                   # 包管理配置
├── pyproject.toml             # 依赖 + pytest + allure 配置（企业主推）
├── requirements.txt           # 依赖包锁定（pip freeze 产出）
├── requirements-dev.txt       # 开发依赖：pytest、black、flake8、allure-pytest
│
├── config/                    # 🔥 企业必分环境配置
│   ├── __init__.py
│   ├── base.yaml              # 公共配置：超时、浏览器、重试、全局变量
│   ├── dev.yaml               # 开发环境：URL、账号、开关
│   ├── qa.yaml                # 测试环境
│   ├── prod.yaml              # 生产环境
│   └── settings.py            # 配置读取封装（统一加载 yaml）
│
├── src/                       # 🔥 源码隔离（企业 src-layout 标准）
│   └── auto/                  # 包名：auto（可改）
│       ├── __init__.py
│       ├── core/              # 核心封装（企业公共底座）
│       │   ├── __init__.py
│       │   ├── base_page.py   # POM 基类：等待、点击、输入、截图、录屏
│       │   ├── base_api.py    # 接口基类：请求、签名、重试、异常封装
│       │   └── exceptions.py  # 自定义异常：元素不存在、登录失败等
│       │
│       ├── utils/             # 🔥 工具层（企业统一抽离）
│       │   ├── __init__.py
│       │   ├── logger.py      # 日志封装：按天切割、控制台+文件、级别控制
│       │   ├── file_io.py     # 文件读写：json/yaml、目录创建、清理
│       │   ├── video.py       # 视频录制封装（playwright 录屏）
│       │   ├── screenshot.py  # 截图封装（含 allure 附件）
│       │   └── common.py      # 通用工具：随机数、时间、加密、参数化
│       │
│       ├── api/               # 业务接口层（封装后端接口）
│       │   ├── __init__.py
│       │   ├── login_api.py   # 登录相关接口
│       │   └── user_api.py    # 用户管理接口
│       │
│       └── pages/             # 🔥 POM 页面对象（UI 元素+操作）
│           ├── __init__.py
│           ├── login_page.py  # 登录页：元素定位+操作方法
│           └── home_page.py   # 首页：元素定位+操作方法
│
├── tests/                     # 🔥 测试用例（镜像 src 结构，企业规范）
│   ├── __init__.py
│   ├── conftest.py            # pytest 全局 fixture：浏览器、page、录屏、截图、日志
│   ├── test_login/            # 模块用例（按业务划分）
│   │   ├── __init__.py
│   │   ├── test_login_success.py
│   │   └── test_login_fail.py
│   └── test_home/
│       ├── __init__.py
│       └── test_home_nav.py
│
├── testdata/                   # 🔥 测试数据（和代码分离）
│   ├── login_data.json         # 登录参数化数据
│   └── user_data.yaml          # 用户数据
│
├── logs/                       # 🔥 日志（运行时生成，git 忽略）
│   ├── framework/              # 框架日志
│   └── cases/                  # 用例日志（按用例名）
│
├── reports/                    # 🔥 测试报告（allure/pytest-html）
│   ├── allure-results/         # allure 原始数据
│   └── html/                   # html 报告
│
├── artifacts/                  # 🔥 视频/截图（playwright 产出，git 忽略）
│   ├── videos/                 # 录屏文件（.webm）
│   └── screenshots/            # 失败截图
│
├── fixtures/                   # 🔥 扩展 fixture（复杂场景）
│   ├── __init__.py
│   └── db_fixture.py           # 数据库 fixture（连接/清理）
│
└── scripts/                    # 🔥 执行脚本（CI/本地运行）
    ├── run_smoke.sh            # 冒烟测试脚本
    └── run_all.sh              # 全量测试脚本
```

## 配置说明

本项目使用 `config/settings.py` 统一加载 YAML 配置，优先级如下：

1. `base.yaml` 公共配置
2. `{env}.yaml` 环境配置（dev / qa / prod）
3. 环境变量覆盖（通过 `TEST_ENV` 设置）

默认环境为 `dev`。

### 切换配置环境

- Windows PowerShell:

```powershell
$env:TEST_ENV = 'qa'
pytest tests/ -v
```

- Linux / macOS:

```bash
export TEST_ENV=qa
pytest tests/ -v
```

### 代码中直接获取配置

```python
from config.settings import get_settings

settings = get_settings()
base_url = settings.get('base.url')
headless = settings.get('browser.headless')
```

## 快速开始

### 1. 安装依赖

```bash
pip install pytest-playwright
playwright install #安装chromium 插件
pip install -r requirements.txt
```

### 2. 运行测试

```bash
pytest tests/ -v
```

### 3. 生成 Allure 报告

```bash
pytest tests/ --alluredir=reports/allure-results
allure serve reports/allure-results
```

## 重要文件说明

| 文件/目录 | 说明 |
| --- | --- |
| .gitignore | 忽略日志、报告、视频、环境文件、虚拟环境等运行时产物 |
| pyproject.toml | 项目依赖与 pytest、allure、black、isort 配置 |
| requirements.txt | 运行依赖锁定 |
| requirements-dev.txt | 开发依赖列表 |
| config/settings.py | YAML 配置加载与环境切换封装 |
| tests/conftest.py | 全局 pytest fixture |
| scripts/ | CI/本地执行脚本 |

## 执行命令-脚本方式

```bash
bash scripts/run_smoke.sh
bash scripts/run_all.sh
pytest tests/test_search/test_baidu_search.py::test_search_and_click_first -v -s
```
## 执行命令-命令行方式

```bash
# 1. 卸载旧版本
pip install -e . 【开发模式】
pip install  . 【发布模式】

# 2. 卸载旧版本
pip uninstall web_ui_auto -y

# 3. 清理构建产物
Remove-Item -Recurse -Force build, dist, *.egg-info -ErrorAction SilentlyContinue

# 4. 重新打包
python setup.py sdist bdist_wheel

# 5. 安装新版本（强制重装以确保脚本生成）
pip install --force-reinstall --no-deps (Get-ChildItem dist\*.whl | Select-Object -First 1).FullName

# 6. 执行命令
web-ui-auto run

# 7. 查找命令位置
where.exe web-ui-auto
```
## 开发指南

1. 页面对象在 `src/auto/pages/`
2. 工具模块在 `src/auto/utils/`
3. 公共基类在 `src/auto/core/`
4. 用例在 `tests/` 对应模块目录
5. 代码格式请使用 `black` 和 `flake8`

## 许可证

MIT

