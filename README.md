# web_ui_auto
这是一个企业级web端UI自动化测试的工程目录结构
目录功能：

pythonPro/                      # 项目根目录（全小写、短名）
├── .gitignore                # 忽略：logs、reports、videos、.env、venv
├── README.md                 # 项目说明、部署、运行命令
├── pyproject.toml            # 依赖 + pytest + allure 配置（大厂主推）
├── requirements.txt           # 依赖包锁定（pip freeze 产出）
├── requirements-dev.txt      # 开发依赖：pytest、black、flake8、allure-pytest
│
├── config/                    # 🔥 大厂必分环境配置
│   ├── __init__.py
│   ├── base.yaml              # 公共配置：超时、浏览器、重试、全局变量
│   ├── dev.yaml               # 开发环境：URL、账号、开关
│   ├── qa.yaml                # 测试环境
│   ├── prod.yaml              # 生产环境
│   └── settings.py            # 配置读取封装（统一加载 yaml）
│
├── src/                       # 🔥 源码隔离（大厂 src-layout 标准）
│   └── auto/                  # 包名：auto（可改）
│       ├── __init__.py
│       ├── core/              # 核心封装（大厂公共底座）
│       │   ├── __init__.py
│       │   ├── base_page.py  # POM 基类：等待、点击、输入、截图、录屏
│       │   ├── base_api.py    # 接口基类：请求、签名、重试、异常封装
│       │   └── exceptions.py # 自定义异常：元素不存在、登录失败等
│       │
│       ├── utils/             # 🔥 工具层（大厂统一抽离）
│       │   ├── __init__.py
│       │   ├── logger.py      # 日志封装：按天切割、控制台+文件、级别控制
│       │   ├── file_io.py     # 文件读写：json/yaml、目录创建、清理
│       │   ├── video.py       # 视频录制封装（playwright 录屏）
│       │   ├── screenshot.py  # 截图封装（含 allure 附件）
│       │   └── common.py      # 通用工具：随机数、时间、加密、参数化
│       │
│       ├── api/                # 业务接口层（封装后端接口）
│       │   ├── __init__.py
│       │   ├── login_api.py   # 登录相关接口
│       │   └── user_api.py    # 用户管理接口
│       │
│       └── pages/              # 🔥 POM 页面对象（UI 元素+操作）
│           ├── __init__.py
│           ├── login_page.py  # 登录页：元素定位+操作方法
│           └── home_page.py   # 首页：元素定位+操作方法
│
├── tests/                      # 🔥 测试用例（镜像 src 结构，大厂规范）
│   ├── __init__.py
│   ├── conftest.py             # pytest 全局 fixture：浏览器、page、录屏、截图、日志
│   ├── test_login/             # 模块用例（按业务划分）
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
├── artifacts/                   # 🔥 视频/截图（playwright 产出，git 忽略）
│   ├── videos/                  # 录屏文件（.webm）
│   └── screenshots/            # 失败截图
│
├── fixtures/                   # 🔥 扩展 fixture（复杂场景）
│   ├── __init__.py
│   └── db_fixture.py           # 数据库 fixture（连接/清理）
│
└── scripts/                    # 🔥 执行脚本（CI/本地运行）
    ├── run_smoke.sh            # 冒烟测试脚本
    └── run_all.sh              # 全量测试脚本
