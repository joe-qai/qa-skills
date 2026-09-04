# 开发环境安装指南

## Python

### Windows
```powershell
# 使用 winget（推荐）
winget install Python.Python.3.12

# 或使用安装包
# 访问 https://www.python.org/downloads/ 下载 Windows installer
```

### macOS
```bash
brew install python@3.12
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

### 验证安装
```bash
python --version  # 应输出 Python 3.12.x
pip --version
```

---

## Node.js

### Windows
```powershell
# 使用 winget（推荐）
winget install OpenJS.NodeJS.LTS

# 或使用安装包
# 访问 https://nodejs.org/zh-cn 下载 LTS 版本
```

### macOS
```bash
brew install node
```

### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

### 验证安装
```bash
node --version   # 应输出 v18.x.x 或更高
npm --version    # 应输出 9.x.x 或更高
```

---

## Go

### Windows
```powershell
# 使用 winget（推荐）
winget install GoLang.Go

# 或使用安装包
# 访问 https://go.dev/dl/ 下载 Windows MSI 安装包
```

### macOS
```bash
brew install go
```

### Linux (Ubuntu/Debian)
```bash
snap install go --classic
# 或从 https://go.dev/dl/ 下载二进制包
```

### 验证安装
```bash
go version  # 应输出 go1.21.x
```

---

## Java (JDK 17+)

### Windows
```powershell
# 使用 winget（推荐）
winget install EclipseAdoptium.Temurin.17.JDK
```

### macOS
```bash
brew install --cask temurin@17
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install openjdk-17-jdk
```

### 验证安装
```bash
java -version     # 应输出 openjdk version "17.x.x"
javac -version    # 应输出 javac 17.x.x
```

---

## Docker

### Windows
1. 确保已启用 WSL2
2. 下载并安装 Docker Desktop for Windows
3. 访问 https://www.docker.com/products/docker-desktop/

```powershell
# 使用 winget（推荐）
winget install Docker.DockerDesktop
```

### macOS
```bash
brew install --cask docker
# 或从 https://www.docker.com/products/docker-desktop/ 下载安装
```

### Linux (Ubuntu/Debian)
```bash
sudo apt install docker.io docker-compose-plugin
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
```

### 验证安装
```bash
docker --version
docker compose version
```

---

## Git

### Windows
```powershell
winget install Git.Git
```

### macOS
```bash
brew install git
```

### Linux
```bash
sudo apt install git
```

---

## SVN (Subversion)

### Windows
```powershell
winget install Apache.Subversion
```

### macOS
```bash
brew install subversion
```

### Linux
```bash
sudo apt install subversion
```

---

## JMeter 5.6.2（性能测试）

### 用途
HTTP/HTTPS 性能测试、压力测试、负载测试。

### 版本与来源
- 版本固定：`apache-jmeter-5.6.2`
- 官方下载：`https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.2.zip`
- 必须校验 SHA-512 或从官方页面获取校验值

### 前置依赖
Java Runtime（JRE 8+ 或 JDK 17+，参考编号 4）

### 安装方式
绿色解压即用，无需安装程序：
```bash
# 解压到目标目录
Expand-Archive -Path "apache-jmeter-5.6.2.zip" -DestinationPath "E:\Test_tool_enviroment\JMeter\"
```

### 环境变量
- `JMETER_HOME`（Machine）= `E:\Test_tool_enviroment\JMeter\apache-jmeter-5.6.2\`
- PATH 追加 `%JMETER_HOME%\bin\`

### 验证
```bash
E:\Test_tool_enviroment\JMeter\apache-jmeter-5.6.2\bin\jmeter.bat -v
# 或
jmeter -v
```

---

## Locust（性能测试）

### 用途
Python 编写的分布式负载测试工具，适合 HTTP/WebSocket 压测，支持 Web UI 和 CLI 模式。

### 版本与来源
- 版本锁定：`locust==2.32.0`
- 官方源：`https://pypi.org/project/locust/`
- 安装方式：`pip install locust==2.32.0`

### 前置依赖
Python 3.10+（编号 1）

### 安装方式
```bash
pip install locust==2.32.0
```

### 环境变量
无需新增环境变量。

### 验证
```bash
locust --version
# 输出示例：locust 2.32.0
```

---

## 离线包管理策略

所有工具安装遵循以下优先级：

1. **本地包优先**：检查 `E:\Tools_Package\<工具名>\` 是否有已校验的离线安装包
   - 运行 `python scripts/check_packages.py <工具名>` 探测
   - 有本地包且 SHA-256 匹配 → 直接使用，无需联网
2. **官方在线兜底**：本地包不存在时从官方源下载
   - Windows: `winget install <winget-id>`
   - 或直接下载官方安装器并校验 SHA-256
3. **禁止行为**：
   - 不得从第三方镜像站下载
   - 不得跳过 SHA-256 校验
   - 不得在用户未确认前联网下载

```powershell
# 安装 WSL 和 Ubuntu
wsl --install

# 查看所有可用的 Linux 发行版
wsl --list --online
```
