# Dev Environment Catalog — 开发环境编号清单

> 编号列表是用户选择的唯一入口。Agent 只安装用户明确选中的编号及其依赖，不旁路安装其他环境。
> 版本号不硬编码：每个环境列出**最近 5 个稳定版本**供用户选择；已有环境时自动推荐兼容版本。

## 编号约定

- 每个环境使用唯一的一级编号（如 `1. Python`、`2. Node.js`），不复用、不合并。
- 新增环境时追加新编号，保持向后兼容。
- 依赖关系在每个编号的 `prereqs` 字段中声明；Agent 自动补齐选中环境的依赖闭包，不擅自安装未声明的依赖。
- **OS 兼容性**：每个环境标注支持的操作系统；若当前系统不在支持列表中，标记 `OS_UNSUPPORTED`，跳过安装并输出原因。
- **已有环境兼容**：若检测到本机已安装某环境，默认推荐与已安装版本兼容的版本范围，不再询问用户选择。

---

## 环境编号清单

### 1. Python

| 字段 | 值 |
|------|---|
| **用途** | 后端运行时，支持 Django / FastAPI / 压测脚本 / Locust / tidevice |
| **可用版本（最近 5 个）** | **3.12.x**（当前主流）/ **3.11.x** / **3.10.x** / **3.9.x** / **3.8.x** |
| **版本选择规则** | 本机无 Python → 推荐 3.12；已有 3.14.x → 可装 3.12 或保持 3.14 路径复用 |
| **官方来源（Windows）** | `https://www.python.org/ftp/python/<VERSION>/python-<VERSION>-amd64.exe` |
| **winget 包名** | `Python.Python.3.12`（其他版本需手动指定 URL） |
| **本地包目录** | `E:\Tools_Package\Python\`（离线安装器 + manifest.json） |
| **安装目录** | `E:\Test_tool_enviroment\Python\`（或官方默认路径） |
| **网络要求** | 无本地包时需外网访问 `python.org` / winget 源 |
| **环境变量** | `PYTHON_HOME`（Machine）；PATH 追加 `%PYTHON_HOME%\` + `%PYTHON_HOME%\Scripts\` |
| **验证命令** | `python --version`、`pip --version` |
| **风险等级** | L1 |

### 2. Node.js

| 字段 | 值 |
|------|---|
| **用途** | 前端运行时，支持 npm/pnpm/yarn；构建 Vue/React/Next.js 项目；Hypium 依赖 |
| **可用版本（最近 5 个）** | **22.x LTS**（当前 LTS）/ **20.x LTS** / **18.x LTS** / **21.x Current** / **16.x** |
| **版本选择规则** | 本机无 Node → 推荐 22 LTS；已有 v22.16.0 → 可升级至最新 22.x 或切换 20.x LTS |
| **官方来源（Windows）** | `https://nodejs.org/dist/v<VERSION>/node-v<VERSION>-x64.msi` |
| **winget 包名** | `OpenJS.NodeJS.LTS`（当前默认 22 LTS） |
| **本地包目录** | `E:\Tools_Package\NodeJs\`（离线安装器或 ZIP + manifest.json） |
| **安装目录** | `E:\Test_tool_enviroment\NodeJs\`（或官方默认路径） |
| **网络要求** | 无本地包时需外网访问 `nodejs.org` / winget 源；执行 `npm install` 访问 `registry.npmjs.org` |
| **环境变量** | PATH 追加 Node.js 安装目录（安装器通常自动配置） |
| **验证命令** | `node --version`、`npm --version` |
| **风险等级** | L1 |

### 3. Go

| 字段 | 值 |
|------|---|
| **用途** | 后端运行时，支持 Gin / Fiber |
| **可用版本（最近 5 个）** | **1.23.x**（当前最新）/ **1.22.x** / **1.21.x** / **1.20.x** / **1.19.x** |
| **版本选择规则** | 本机无 Go → 推荐 1.23；已有旧版本 → 可选择覆盖或保留旧版并行安装 |
| **官方来源（Windows）** | `https://go.dev/dl/go<VERSION>.windows-amd64.msi` |
| **winget 包名** | `GoLang.Go` |
| **本地包目录** | `E:\Tools_Package\Go\`（ZIP 解压包 + manifest.json） |
| **安装目录** | `E:\Test_tool_enviroment\Go\`（或官方默认路径） |
| **网络要求** | 无本地包时需外网访问 `go.dev/dl/` / winget 源 |
| **环境变量** | `GOROOT`（Machine）；PATH 追加 `%GOROOT%\bin\` |
| **验证命令** | `go version` |
| **风险等级** | L1 |

### 4. Java JDK

| 字段 | 值 |
|------|---|
| **用途** | 后端运行时（Spring Boot）、JMeter 运行依赖 |
| **可用版本（最近 5 个）** | **21.x LTS**（最新 LTS）/ **17.x LTS** / **11.x LTS** / **22.x Current** / **8.x** |
| **版本选择规则** | JMeter 5.6.2 支持 JDK 8+，推荐 17 或 21；Spring Boot 3.x 需 JDK 17+ |
| **官方来源（Windows）** | `https://api.adoptium.net/v3/binary/latest/<VERSION>/ga/windows/x64/jdk/hotspot/normal/eclipse` |
| **winget 包名** | `EclipseAdoptium.Temurin.17.JDK`（或替换版本号） |
| **本地包目录** | `E:\Tools_Package\Java\`（JDK ZIP 或 MSI + manifest.json） |
| **安装目录** | `E:\Test_tool_enviroment\Java\`（或官方默认路径） |
| **网络要求** | 无本地包时需外网访问 `adoptium.net` / winget 源 |
| **环境变量** | `JAVA_HOME`（Machine）；PATH 追加 `%JAVA_HOME%\bin\` |
| **验证命令** | `java -version`、`javac -version` |
| **风险等级** | L1 |

### 5. Docker Desktop

| 字段 | 值 |
|------|---|
| **用途** | 容器化运行环境，支持 docker-compose 编排 |
| **版本策略** | 始终安装最新版（Docker 不开放历史版本下载） |
| **官方来源（Windows）** | `https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe` |
| **winget 包名** | `Docker.DockerDesktop` |
| **本地包目录** | `E:\Tools_Package\Docker\`（ISO 或 EXE + manifest.json） |
| **安装目录** | 官方固定路径（默认），不强制改到 E 盘 |
| **网络要求** | 首次启动需联网激活；安装包下载需外网 |
| **前置依赖** | Windows 10/11 需 WSL2（编号 8）；安装后需重启 |
| **环境变量** | Docker Desktop 自行管理，无需手动配置 |
| **验证命令** | `docker --version`、`docker compose version` |
| **风险等级** | L1（首次启动需管理员权限） |

### 6. Git

| 字段 | 值 |
|------|---|
| **用途** | 版本控制 |
| **可用版本（最近 5 个）** | **2.47.x**（当前最新）/ **2.46.x** / **2.45.x** / **2.44.x** / **2.43.x** |
| **版本选择规则** | 本机无 Git → 推荐最新版；已有 Git → 可升级或保持原版本 |
| **官方来源（Windows）** | `https://github.com/git-for-windows/git/releases/download/v<VERSION>/Git-<VERSION>-64-bit.exe` |
| **winget 包名** | `Git.Git` |
| **本地包目录** | `E:\Tools_Package\Git\`（安装器 + manifest.json） |
| **安装目录** | 官方固定路径（默认） |
| **网络要求** | 无本地包时需外网访问 `github.com` / winget 源 |
| **环境变量** | PATH 追加 Git 安装目录（通常安装器自动配置） |
| **验证命令** | `git --version` |
| **风险等级** | L0 |

### 7. SVN（Subversion）

| 字段 | 值 |
|------|---|
| **用途** | 版本控制（Subversion） |
| **可用版本（最近 5 个）** | **1.14.x**（当前最新）/ **1.13.x** / **1.12.x** / **1.11.x** / **1.10.x** |
| **版本选择规则** | 本机无 SVN → 推荐 1.14；已有 SVN → 可选择升级 |
| **官方来源（Windows）** | `https://downloads.apache.org/subversion/<VERSION>/win64/apache-subversion-<VERSION>-bin.zip` |
| **winget 包名** | `Apache.Subversion` |
| **本地包目录** | `E:\Tools_Package\SVN\`（ZIP 解压包 + manifest.json） |
| **安装目录** | `E:\Test_tool_enviroment\SVN\` |
| **网络要求** | 无本地包时需外网访问 `downloads.apache.org` / winget 源 |
| **环境变量** | PATH 追加 SVN bin 目录 |
| **验证命令** | `svn --version` |
| **风险等级** | L0 |

### 8. WSL

| 字段 | 值 |
|------|---|
| **用途** | Windows 子系统 for Linux（Docker Desktop 前置依赖） |
| **版本策略** | 系统内置，版本随 Windows 更新，不可手动选择 |
| **安装命令** | `wsl --install`（需管理员权限） |
| **网络要求** | 需要外网下载 Linux 发行版（默认 Ubuntu） |
| **环境变量** | 无新增环境变量 |
| **验证命令** | `wsl --version`、`wsl -l -v` |
| **风险等级** | L1（重启后生效） |

### 9. Apache JMeter

| 字段 | 值 |
|------|---|
| **用途** | HTTP/HTTPS 性能测试、压力测试 |
| **可用版本（最近 5 个）** | **5.6.2**（当前最新稳定）/ **5.6.1** / **5.5.1** / **5.4.3** / **5.4.1** |
| **版本选择规则** | JMeter 5.6.x 需要 JDK 8+；推荐 5.6.2 搭配 JDK 17/21 |
| **官方来源** | `https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-<VERSION>.zip` |
| **本地包目录** | `E:\Tools_Package\JMeter\apache-jmeter-<VERSION>\`（ZIP 解压包 + manifest.json） |
| **安装目录** | `E:\Test_tool_enviroment\JMeter\apache-jmeter-<VERSION>\`（绿色解压即用） |
| **前置依赖** | Java Runtime（编号 4）；版本不强制绑定，JDK 8+ 即可 |
| **网络要求** | 无本地包时需外网访问 `archive.apache.org`；Java 缺失时还需 Adoptium 源 |
| **环境变量** | 系统级 PATH 追加 JMeter `bin` 目录；`JMETER_HOME`（Machine） |
| **验证命令** | `<JMeter_bin_dir>\jmeter.bat -v` 或 `jmeter -v`，检查 `java -version` |
| **风险等级** | L1（需 Java 支持） |

### 10. Locust

| 字段 | 值 |
|------|---|
| **用途** | Python 编写的分布式负载测试工具，适合 HTTP/WebSocket 压测 |
| **可用版本（最近 5 个）** | **2.32.x**（当前最新）/ **2.31.x** / **2.30.x** / **2.29.x** / **2.28.x** |
| **版本选择规则** | Locust 2.x 支持 Python 3.8+；建议安装最新 2.32.x |
| **官方来源** | `https://pypi.org/project/locust/#files` |
| **安装方式** | `pip install locust==<VERSION>`（需 Python 3.10+，编号 1 已安装则复用） |
| **本地包目录** | `E:\Tools_Package\Locust\`（wheel 文件 + manifest.json） |
| **安装目录** | Python site-packages（随 Python 安装目录），无需独立目录 |
| **前置依赖** | Python（编号 1） |
| **网络要求** | 无本地 wheel 时需外网访问 `pypi.org`；离线方案：提供完整 wheelhouse |
| **环境变量** | 无需新增环境变量（pip 安装的命令行工具自动在 PATH 中） |
| **验证命令** | `locust --version` |
| **风险等级** | L1（仅 pip 安装，无系统级变更） |

### 11. Android ADB

| 字段 | 值 |
|------|---|
| **用途** | Android 设备调试、APP 自动化测试、性能数据采集 |
| **版本策略** | platform-tools 版本随 Android SDK 发布，通常只安装最新稳定版 |
| **官方来源（Windows）** | `https://dl.google.com/android/repository/platform-tools-latest-windows.zip` |
| **macOS 来源** | `brew install android-platform-tools` |
| **本地包目录** | `E:\Tools_Package\Android-ADB\`（官方 ZIP + manifest.json） |
| **安装目录** | `E:\Test_tool_enviroment\Android-ADB\platform-tools\` |
| **前置依赖** | 无 |
| **网络要求** | 无本地包时需外网访问 `dl.google.com`；无设备时可离线使用 |
| **环境变量** | PATH 追加 `platform-tools` 目录 |
| **验证命令** | `adb version`、`adb devices` |
| **风险等级** | L0 |

### 12. Huawei HDC（HarmonyOS Device Connector）

| 字段 | 值 |
|------|---|
| **用途** | 华为鸿蒙设备调试、APP 自动化测试 |
| **版本策略** | 版本随 DevEco Studio 发布，建议安装最新稳定版 |
| **官方来源** | `https://developer.huawei.com/consumer/cn/deveco-studio/`（DevEco Studio 内含） |
| **本地包目录** | `E:\Tools_Package\HDC\`（hdc.exe + manifest.json） |
| **安装目录** | `E:\Test_tool_enviroment\HDC\` |
| **前置依赖** | 无（独立工具） |
| **网络要求** | 无本地包时需外网访问 `huawei.com`；需华为开发者账号 |
| **环境变量** | PATH 追加 HDC bin 目录 |
| **验证命令** | `hdc w`（列出连接设备）、`hdc info` |
| **风险等级** | L0 |

### 13. tidevice（Apple iOS 设备调试）

| 字段 | 值 |
|------|---|
| **用途** | iOS 设备调试、APP 自动化测试 |
| **可用版本（最近 5 个）** | **0.13.x**（当前最新）/ **0.12.x** / **0.11.x** / **0.10.x** / **0.9.x** |
| **版本选择规则** | tidevice 0.12+ 支持较新的 iOS 版本；推荐安装最新版 |
| **官方来源** | `https://pypi.org/project/tidevice/` |
| **安装方式** | `pip install tidevice`（需 Python 3.8+，编号 1 已安装则复用） |
| **本地包目录** | `E:\Tools_Package\tidevice\`（wheel 文件 + manifest.json） |
| **安装目录** | Python site-packages（随 Python 安装目录） |
| **前置依赖** | Python（编号 1）；Windows 下需 libimobiledevice |
| **网络要求** | 无本地 wheel 时需外网访问 `pypi.org` |
| **环境变量** | 无需新增环境变量 |
| **验证命令** | `tidevice list`、`tidevice info` |
| **风险等级** | L1（pip 安装） |

### 14. Hypium（华为鸿蒙测试框架）

| 字段 | 值 |
|------|---|
| **用途** | 鸿蒙 APP 自动化测试框架 |
| **可用版本（最近 5 个）** | 版本号随鸿蒙 SDK 发布，建议安装最新稳定版 |
| **官方来源** | `https://www.npmjs.com/package/@hmos/hypium` |
| **安装方式** | `npm install -g @hmos/hypium`（需 Node.js 18+，编号 2 已安装则复用） |
| **本地包目录** | `E:\Tools_Package\Hypium\`（npm 离线包 + manifest.json） |
| **安装目录** | Node.js 全局模块目录 |
| **前置依赖** | Node.js（编号 2，需 18+） |
| **网络要求** | 无本地 npm 包时需外网访问 `registry.npmjs.org`；鸿蒙开发需华为账号 |
| **环境变量** | 无需新增环境变量（npm 全局包自动在 PATH 中） |
| **验证命令** | `hypium --version` |
| **风险等级** | L1（npm 安装） |

---

## 版本选择交互流程

当用户请求安装某个环境时，Agent 按以下顺序处理：

1. **探测本机是否已安装**：运行 `detect_env.py` 获取当前版本
2. **若已安装**：
   - 显示当前版本，询问用户"是否安装新版本？"
   - 若选择安装，列出最近 5 个可用版本供选择
   - 若选择不安装，直接跳过该环境
3. **若未安装**：
   - 列出最近 5 个可用版本，默认推荐最新版
   - 用户可指定版本号，或按回车使用默认推荐
4. **依赖版本兼容**：
   - JMeter 推荐 JDK 17/21（不强制特定版本，只要 8+ 即可）
   - Locust 推荐 Python 3.10+（与本机 Python 版本兼容）
   - Hypium 需要 Node.js 18+（若本机 Node 版本 < 18，先提示升级 Node）
   - tidevice 需要 Python 3.8+（通常满足）

---

## 编号选择规则

- 用户通过编号（如 `1, 3, 9`）或名称（如 `Python, JMeter`）选择要安装的环境。
- Agent 自动解析编号并补齐依赖闭包（如选 9 自动带 4）。
- 未选中的编号不安装、不探测、不下载。
- `all` 安装全部缺失环境；`skip` 跳过安装直接进行项目脚手架。

## 依赖关系表

| 编号 | 名称 | 依赖编号 | 兼容性说明 |
|------|------|---------|-----------|
| 1 | Python | — | 推荐 3.12；已有版本可复用 |
| 2 | Node.js | — | 推荐 22 LTS；Hypium 需 18+ |
| 3 | Go | — | 推荐 1.23 |
| 4 | Java JDK | — | 推荐 17 或 21 LTS |
| 5 | Docker Desktop | 8 (WSL) | Windows 需 WSL2；macOS 无此依赖 |
| 6 | Git | — | — |
| 7 | SVN | — | — |
| 8 | WSL | — | 仅 Windows |
| 9 | JMeter | 4 (Java) | Java 8+ 即可，推荐 17/21 |
| 10 | Locust | 1 (Python) | Python 3.8+；推荐与本机 Python 版本兼容 |
| 11 | ADB | — | — |
| 12 | HDC | — | — |
| 13 | tidevice | 1 (Python) | Python 3.8+ |
| 14 | Hypium | 2 (Node.js) | Node.js 18+ |

## OS 兼容性总表

| 编号 | Windows | macOS | Linux |
|------|---------|-------|-------|
| 1 Python | ✅ | ✅ | ✅ |
| 2 Node.js | ✅ | ✅ | ✅ |
| 3 Go | ✅ | ✅ | ✅ |
| 4 Java | ✅ | ✅ | ✅ |
| 5 Docker | ⚠️ 需 WSL2 | ✅ | ✅ |
| 6 Git | ✅ | ✅ | ✅ |
| 7 SVN | ✅ | ✅ | ✅ |
| 8 WSL | ✅ | ❌ 不适用 | ❌ 不适用 |
| 9 JMeter | ✅ | ✅ | ✅ |
| 10 Locust | ✅ | ✅ | ✅ |
| 11 ADB | ✅ | ✅ | ✅ |
| 12 HDC | ✅ | ✅ | ❌ 不支持 |
| 13 tidevice | ⚠️ 有限支持 | ✅ | ❌ 不支持 |
| 14 Hypium | ✅ | ✅ | ❌ 不支持 |
