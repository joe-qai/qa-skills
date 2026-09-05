---
name: github-discover
description: Use when the user wants to discover, search, clone, or deeply analyze open-source projects on GitHub — including trending repos, fuzzy keyword search, exact repository lookup, and technical framework extraction for learning purposes. Triggers on phrases like "搜一下GitHub热门项目", "看看有没有类似xxx的开源库", "帮我把这个项目clone下来研究", "这个项目用什么技术栈", "帮我调研一下XX领域的开源方案".
---

# GitHub Discover & Research

## 概述

这是一个 GitHub 开源项目发现与深度研究工具。支持四种模式：

1. **热门趋势发现** — 搜索当前热门/趋势开源项目（纯 API，无需 clone）
2. **模糊搜索** — 按关键词模糊查找相关仓库（纯 API，无需 clone）
3. **精确研究** — 先通过 API 获取元数据，分析 README 和topics；**仅当用户明确要求 clone 或需要读取源码时**才执行 clone，clone 完成后做技术拓印并生成报告，研究完成后提示用户是否保留本地副本
4. **每日热榜发现** — 自动挑选一个近期热门项目，完整走 clone → 分析 → 生成公众号/知乎长文 → 生成视觉卡片 → 输出到日期目录的流水线

所有操作均通过 GitHub REST API v3（无需 token 可匿名查询，建议配置 token 提升限频）。

**核心原则：Clone 是可选操作，只在用户明确要求或研究需要时才执行。研究完成后可清理沙箱。**

---

## 触发场景速查

| 用户意图 | 匹配关键词 | 推荐模式 |
|---------|-----------|---------|
| "看看最近热门的AI框架" | 热门、趋势、热门项目 | Mode A |
| "找一下Python爬虫框架" | 找找、看看有没有、推荐一个 | Mode B |
| "帮我调研一下这个项目" | 技术栈、依赖、框架、架构 | Mode C（API 分析，不 clone）|
| "把langchain clone 下来研究" | clone、拉下来、本地研究 | Mode C（需 clone）|
| "深入看看这个项目的源码" | 源码分析、看代码、深入分析 | Mode C（需 clone）|
| "今天的GitHub热榜项目是什么" | 每日热榜、今天热门、今日开源 | Mode D |
| "生成一篇公众号文章介绍这个项目" | 写篇文章、发公众号、生成推文 | Mode D |

---

## GitHub API 基础

### 端点与限频

```
无认证：60 次/小时
有 token：5000 次/小时
```

通过环境变量 `GITHUB_TOKEN` 或手动传入即可启用认证模式。

### 缓存策略

免费 token 限频严重，所有查询结果缓存至本地 JSON 文件：

```
<工作目录>/.github_cache/<query_hash>.json
```

缓存有效期 30 分钟；若缓存命中则直接读取，跳过 API 调用。

缓存脚本：见 `scripts/github_api.py`。

---

## Mode A：热门趋势发现

### 目标

按领域/语言/时间维度发现当前热门开源项目，生成结构化发现报告。

### 步骤

1. 确认用户关注的**领域**（如 AI、Web、DevOps、嵌入式）和**语言**（可选）
2. 调用 GitHub Search API：
   ```
   GET https://api.github.com/search/repositories
     ?q=<关键词>&sort=stars&order=desc&per_page=20
   ```
   热门相关关键词示例：
   - AI/LLM：`q=large-language-model OR llm OR agent framework`
   - 嵌入式：`q=rtos OR nrf OR esp32 OR zephyr`
   - Web：`q=next.js OR svelte OR fastapi`
   - 通用热门：不设关键词，直接用 `sort=created` + 时间过滤
3. 若 token 限频，先用缓存；缓存不存在时告知用户等待或提供 token
4. 输出结果：

```markdown
## 🔥 热门项目发现：[领域/语言]

| # | 仓库 | ⭐ Stars | 描述 | 语言 | 更新时间 |
|---|------|---------|------|------|---------|
| 1 | owner/repo | 12k | 一句话介绍 | Python | 2026-09-01 |
```

5. 询问用户是否对某个项目进入 Mode C 深度研究

---

## Mode B：模糊搜索

### 目标

用户给出一个模糊需求（"我想要一个Rust写的ORM"），Agent 帮助找到最匹配的开源项目。

### 步骤

1. 解析用户意图，提炼**搜索关键词**（技术名、功能描述、应用场景）
2. 构造 search query，优先使用 GitHub Search 语法：
   - `language:python stars:>1000` — 按语言过滤
   - `topic:llm topic:agent` — 按主题过滤
   - `>1y` / `<2024-01-01` — 时间范围
   - 组合示例：`q=rust+orm&sort=stars&order=desc&language=rust`
3. 调用搜索 API（同 Mode A）
4. 按 relevance + stars + 近期活跃度综合排序，输出 Top 5–10
5. 展示卡片式结果，每个仓库显示：名称、Stars、描述、语言、最近提交、是否活跃

```markdown
## 🔍 搜索结果：[关键词]

### 1. tokio-rs/tokio ⭐ 28k
- **描述**：Rust 异步运行时，生产级任务调度
- **语言**：Rust
- **最近更新**：2026-09-03（活跃）
- **链接**：https://github.com/tokio-rs/tokio
```

6. 主动询问："要对哪个项目进行深度研究？（输入序号或仓库名）"

---

## Mode C：精确研究 + 按需 Clone + 技术拓印

### 目标

对指定仓库执行：API 元数据分析 → （按需 clone）→ 技术拓印 → 生成完整研究报告。
**clone 不是默认步骤，仅在以下情况执行：**
- 用户明确要求 clone（"clone下来"、"拉下来"、"本地研究"等）
- 需要读取具体源代码做深度分析（API 无法提供）

### 步骤

#### Step 1：精确查找（始终执行，无需 clone）

确认仓库地址，格式：`owner/repo` 或完整 URL。

调用 API 获取仓库元数据：
```
GET https://api.github.com/repos/{owner}/{repo}
```

关键返回字段：`description`, `stargazers_count`, `language`, `topics`, `default_branch`, `created_at`, `updated_at`, `license`, `open_issues_count`, `has_wiki`, `has_pages`。

#### Step 2：（可选）按需 Clone 为沙箱环境

**仅在用户明确要求或需要源码深度分析时执行。**

克隆仓库到 `<工作目录>/.github_sandbox/<repo_name>/`（用 `.github_sandbox` 明确标识这是临时研究沙箱，而非长期项目目录）：
```bash
git clone --depth 1 https://github.com/{owner}/{repo}.git .github_sandbox/<repo_name>
```

克隆前向用户说明：
```
准备将 owner/repo 克隆为研究沙箱：
路径：./.github_sandbox/<repo_name>/
大小估算：约 XX MB
研究完成后可以删除此目录。
是否继续？
```

**沙箱清理**：研究完成后主动询问用户是否保留本地副本，若不保留则删除 `.github_sandbox/<repo_name>/` 目录。

#### Step 3：技术拓印分析

在克隆目录（或通过 API 的 README/Topics 字段补充信息），按以下顺序读取文件，输出结构化分析：

**3.1 依赖配置文件（必须）**

| 语言 | 文件路径 |
|------|---------|
| Python | `pyproject.toml`, `setup.py`, `requirements.txt` |
| JavaScript/TypeScript | `package.json` |
| Rust | `Cargo.toml` |
| Go | `go.mod` |
| Java/Kotlin | `pom.xml`, `build.gradle` |
| C# | `.csproj` |
| 多语言 | 检查是否存在 monorepo 结构（`packages/`, `apps/`） |

解析主要依赖，提取：框架名、版本范围、是否锁定版本。

**3.2 README 提取**

读取 `README.md` / `README.rst` / `README.zh-CN.md`，提取：
- 项目定位/一句话介绍
- 核心功能列表
- 快速开始命令
- 架构图（若有）

**3.3 目录结构分析**

扫描顶层目录，识别：
- `src/`, `lib/`, `app/` → 源码入口
- `tests/`, `__tests__/` → 测试框架
- `.github/workflows/` → CI/CD 工具链
- `docker-compose.yml`, `Dockerfile` → 容器化方式
- `docs/`, `website/` → 文档系统
- `Makefile`, `justfile` → 构建工具

**3.4 CI/CD 与工程实践**

检查以下文件判断工程成熟度：
- `.github/workflows/*.yml` → GitHub Actions
- `Jenkinsfile` → Jenkins
- `.gitlab-ci.yml` → GitLab CI
- `codecov.yml`, `.coveragerc` → 覆盖率工具
- `pre-commit-config.yaml` → 代码格式化

**3.5 License 与贡献规范**

读取 `LICENSE` 文件和 `CONTRIBUTING.md`，记录许可类型和贡献要求。

#### Step 4：生成研究报告

将分析报告保存至 `<工作目录>/.github_research/<repo_name>/report.md`，格式如下：

```markdown
# [Repo Name] — 技术拓印报告

## 项目概览
- **仓库**：owner/repo
- **链接**：https://github.com/owner/repo
- **Stars**：N,xxx | **Forks**：N | **Open Issues**：N
- **语言**：主要语言 / 次要语言
- **许可证**：MIT / Apache-2.0 / ...
- **最近更新**：YYYY-MM-DD
- **定位**：[从 README 提取的一句话]

## 技术栈
### 核心框架
| 框架 | 版本 | 用途 |
|------|------|------|
| FastAPI | ^0.110 | Web 服务 |
| Pydantic | ^2.5 | 数据校验 |

### 依赖概览
- 直接依赖：N 个
- 开发依赖：N 个
- 类型：[列出分类，如 Web框架、ORM、测试工具等]

## 项目结构
```
├── src/           # 核心源码
├── tests/         # pytest 单元测试
├── .github/       # CI/CD（GitHub Actions）
├── docs/          # 文档（MkDocs）
└── pyproject.toml # 依赖管理
```

## 工程实践
- **CI**：GitHub Actions（pytest + mypy + ruff）
- **覆盖率**：pytest-cov，目标 80%
- **代码质量**：ruff（lint）+ black（格式化）+ pre-commit
- **容器化**：Dockerfile + docker-compose
- **版本管理**：semantic-release / changelog

## 快速开始
[从 README 提取的核心运行命令]

## 学习建议
- 入门路径：README → 核心模块 → 测试 → PR 代码
- 值得关注的 PR：[#123 重构事件循环, #456 新增...]
- 潜在扩展点：[根据代码结构推断]
```

#### Step 5：后续跟进与沙箱清理

询问用户：
- 是否需要继续分析子模块或特定目录？
- 是否需要对比多个同类项目？
- 是否需要将此项目加入持续跟踪清单？
- **沙箱清理**：研究用的 `.github_sandbox/<repo_name>/` 是否保留？若不保留可删除以释放空间。

---

## Mode D：每日热榜发现 + 自动生成公众号文章

### 目标

每天自动挑选一个近期热门项目，完成 clone → 技术拓印 → 生成公众号/知乎风格长文 → 生成视觉卡片图 → 输出到以日期命名的目录。

### 触发词

"今天的GitHub热榜"、"每日开源推荐"、"生成一篇公众号推文"、"帮我写一篇项目介绍"

### 步骤

#### Step 1：挑选项目

调用 daily_discover.py 的 dry-run 模式先看结果：
```bash
python scripts/daily_discover.py --language python --min-stars 1000 --dry-run
```

根据返回的项目信息，向用户确认选择：
```
今日候选项目：owner/repo ⭐ N,xxx
描述：xxxxxx
是否用这个项目生成文章？
```

#### Step 2：执行完整流水线

用户确认后运行：
```bash
python scripts/daily_discover.py \
  --language <语言> \
  --min-stars <最低星标数> \
  --output-dir <输出目录>
```

流水线会自动：
1. 搜索最近 30 天内创建的、stars 最高的项目
2. Clone 到 `.github_sandbox/<repo>/`（depth 1）
3. 运行 `analyze_repo.py` 提取技术栈
4. 运行 `blog_post_generator.py` 生成公众号/知乎长文
5. 运行 `generate_image.py` 生成 800×520 技术栈卡片图
6. 保存 `meta.json` 到输出目录
7. 自动清理沙箱目录

#### Step 3：输出产物

```
<output-dir>/<YYYY-MM-DD>/
├── blog.md          # 公众号/知乎长文
├── card.png         # 800×520 技术栈卡片图
└── meta.json        # 项目元数据 + 分析结果
```

#### Step 4：展示结果

向用户展示：
- 文章标题和开头段落（让用户判断是否符合预期）
- 卡片图路径
- 询问是否需要调整（如更换项目、修改风格等）

### 默认参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--language` | 不限制 | 可按语言筛选（python/rust/ts 等）|
| `--min-stars` | 500 | 最低星标数过滤 |
| `--output-dir` | `daily_output/<今日日期>/` | 输出目录 |
| `--dry-run` | false | 仅预览，不 clone |

### 输出文章风格

- **平台**：微信公众号 / 知乎
- **语气**：网感风 — 有观点、有钩子、带 emoji，适合技术社区传播
- **结构**：钩子开头 → 项目定位 → 技术栈拆解 → 架构亮点 → 值不值得看的结论
- **图片**：技术栈卡片图可作为文章配图插入

详细模板参考 `references/blog_templates.md`。

---

## 脚本参考

### `scripts/github_api.py`

封装 GitHub API 调用，含缓存逻辑：

```python
"""
usage: python scripts/github_api.py <endpoint> [args...]

endpoints:
  search <query> [--sort stars] [--lang python] [--page N]
  repo <owner>/<repo>
  trends [--language python] [--since daily|weekly|monthly]
"""
```

关键行为：
- 读取 `GITHUB_TOKEN` 环境变量（可选）
- 缓存路径：`./.github_cache/`，文件名取 query hash
- 缓存 TTL：1800 秒
- 输出 JSON 到 stdout

### `scripts/daily_discover.py`

每日热榜完整流水线，一键完成：选项目 → clone → 分析 → 写文章 → 出图 → 清理：
```bash
python scripts/daily_discover.py [--language python] [--min-stars 500] [--dry-run] [--output-dir ./daily_output/]
```

### `scripts/blog_post_generator.py`

从 repo 元数据 + 分析报告生成公众号/知乎风格长文：
```bash
python scripts/blog_post_generator.py --repo-meta <json> --analysis <json> --output <path.md>
```

### `scripts/generate_image.py`

生成 800×520 技术栈卡片图（纯 Pillow，无 matplotlib 依赖）：
```bash
python scripts/generate_image.py --repo-meta <json> --analysis <json> --output card.png
```

### `scripts/analyze_repo.py`

对已克隆的仓库执行技术拓印：

```python
"""
usage: python scripts/analyze_repo.py <repo_path> [--output report.md]
"""
```

读取仓库目录，按 Mode C Step 3 的逻辑输出分析报告。

---

## 注意事项

1. **不要假设 token 存在**：无 token 时 API 限频 60/hour，频繁查询会触发 403。此时先检查缓存，缓存未命中则提醒用户配置 token 或耐心等待。
2. **Clone 是按需操作**：默认只做 API 层面的元数据分析（README、Topics、Stars 等），不自动 clone。**仅在用户明确要求或需要源码分析时才 clone**。
3. **沙箱隔离**：clone 的研究目录统一放在 `.github_sandbox/` 下，与项目代码区分，研究完成后可整体清理。
4. **`--depth 1` 是默认策略**：clone 时仅拉取最新 commit，大幅减少时间和磁盘占用。若用户需要历史，显式询问后再移除该参数。
5. **不要自动执行危险操作**：clone 本身是安全的，但不在本 Skill 范围内执行 `npm install`、`pip install -e .`、构建或运行测试。除非用户明确要求。
6. **技术拓印是只读分析**：只读取文件和依赖声明，不修改仓库任何内容。
7. **多项目对比**：当用户同时关注多个同类项目时，并行搜索，然后在报告中以对比表格形式呈现。

---

## 快速命令速查

```bash
# 搜索热门项目（纯 API，无 clone）
python scripts/github_api.py search "llm agent framework" --sort stars --lang python

# 查看具体仓库元数据（纯 API，无 clone）
python scripts/github_api.py repo "langchain-ai/langchain"

# 趋势项目（按时间筛选热门）
python scripts/github_api.py trends --since weekly

# 仅当需要源码分析时才 clone + 技术拓印
git clone --depth 1 https://github.com/langchain-ai/langchain.git .github_sandbox/langchain
python scripts/analyze_repo.py .github_sandbox/langchain --output .github_research/langchain/report.md
# 研究完成后清理沙箱
rm -rf .github_sandbox/langchain

# 一键每日热榜发现 + 生成公众号文章 + 卡片图
python scripts/daily_discover.py --language python --min-stars 1000
# 输出到 daily_output/2026-09-05/blog.md + card.png + meta.json
```
