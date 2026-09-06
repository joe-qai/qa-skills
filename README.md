# 🧪 QA-Skills

AI Agent 驱动的软件测试技能集合，面向 iFlow CLI，覆盖软件测试全生命周期——从需求分析到测试执行，共 **21 个专业技能**。

## ✨ 技能一览

| 技能 | 用途 | 关键命令/资源 |
|------|------|----------|
| **requirements-analyzer** | 从 Excel/PDF/PNG/Word/TXT 提取需求 | references/ |
| **requirements-analysis** | 多轮对话式需求分析，EPIC 分解与优先级排序 | references/ |
| **analyze-requirements** | 需求分析全流程编排（自动调度 Agent） | — |
| **testcase-planner** | 需求→测试规划（ITEM/POINT 层级拆解） | `parse_plan.py` |
| **testcase-generator** | 测试点→结构化测试用例（Markdown/Excel/XMind） | `validate.py`, `to_excel.py`, `testcase_to_xmind.py` |
| **doc-based-testcase-generator** | 基于 PRD/接口文档直接生成测试用例 | — |
| **test-effort-estimator** | 测试工作量评估与 Excel 报告 | `generate_excel.py` |
| **webapp-testing** | Playwright 驱动的 Web 应用测试 | `with_server.py` |
| **agent-browser** | 浏览器自动化 CLI（导航/填表/截图/数据提取） | `npx agent-browser` |
| **lanhu-design** | 蓝湖设计稿与 Axure 原型分析 | MCP Server |
| **skill-creator** | 创建、评估与迭代优化技能 | `run_eval.py`, `quick_validate.py` |
| **ui-ux-pro-max** | UI/UX 设计智能（50+风格/161配色/10技术栈） | 50+ styles, 161 palettes |
| **theme-factory** | 幻灯片/文档/落地页主题应用 | 10 preset themes |
| **doc-coauthoring** | 文档协作工作流（PRD/设计文档/提案） | — |
| **huashu-nuwa** | 女娲造人：人物思维框架蒸馏与 Skill 生成 | examples/ |
| **prompt-engineer** | Prompt 工程：设计/优化/评估 LLM Prompts | references/ |
| **xlsx** | Excel 处理：创建/编辑/数据分析 | `recalc.py` |
| **pdf** | PDF 处理：提取/合并/分割/表单填写 | pypdf, pdfplumber |
| **pptx** | PPT 处理：创建/编辑/缩略图生成 | `thumbnail.py`, `markitdown` |
| **github-discover** | GitHub 搜索 + 每日热榜文章生成 | `github_api.py`, `daily_discover.py` |
| **zentao-bug-submitter** | 禅道 Bug 自动提交（REST API v1） | `zentao_client.py` |

## 🔄 完整工作流

```
需求文档 ──→ 需求分析 ──→ 测试规划 ──→ 用例生成 ──→ 测试执行 ──→ 工作量评估
              │              │              │              │
   requirements-    testcase-     testcase-     webapp-     test-effort-
   analyzer/        planner       generator     testing     estimator
   analysis/
```

### 测试技能（核心）

```
requirements-analyzer/      testcase-planner/      testcase-generator/
analyze-requirements/       └── parse_plan.py      ├── validate.py
                                                      to_excel.py
                                                      testcase_to_xmind.py
```

### 设计与文档技能

```
lanhu-design/               ui-ux-pro-max/         doc-coauthoring/
MCP Server                  50+ styles             PRD/提案/设计文档
                             161 palettes

theme-factory/              pptx/                  pdf/
10 preset themes            thumbnail.py            pypdf
                              markitdown
```

### 平台与工程技能

```
agent-browser/              webapp-testing/         skill-creator/
npx agent-browser           with_server.py          run_eval.py
                                                      quick_validate.py
```

### 辅助技能

```
xlsx/                       huashu-nuwa/            prompt-engineer/
recalc.py                   人物思维蒸馏             references/

github-discover/
GitHub 搜索 + 每日热榜文章生成
```

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js（agent-browser 需要）
- LibreOffice（xlsx 公式重算可选）

### 安装依赖

```bash
pip install pandas openpyxl python-docx playwright pypdf pdfplumber
playwright install chromium
```

### 验证安装

```bash
python -c "import pandas, openpyxl, docx, playwright; print('All dependencies OK')"
```

## 📖 使用指南

### 1. 需求分析

从各类文档中提取结构化需求：

- **requirements-analyzer**：支持 Excel、PNG、PDF、Word、TXT 格式，输出功能需求、非功能需求、业务规则、依赖关系图
- **requirements-analysis**：对话式需求细化，支持 EPIC→需求→用户故事分解，MoSCoW/RICE/Kano 优先级排序
- **analyze-requirements**：全流程编排，自动判断复杂度并调度 Agent

### 2. 测试规划

将需求拆解为测试项（ITEM）和测试点（POINT）：

```bash
python testcase-planner/scripts/parse_plan.py --help
```

### 3. 测试用例生成

基于测试点生成结构化用例，支持计划驱动和文档驱动两种模式：

```bash
# 验证单条用例格式
python testcase-generator/scripts/validate.py --single "test-case/ITEM/POINT.md"

# 批量验证
python testcase-generator/scripts/validate.py "test-case/"

# 重复检查
python testcase-generator/scripts/validate.py "test-case/" --check-duplicates

# 导出为 Excel
python testcase-generator/scripts/to_excel.py "test-case/" -o "export.xlsx"

# 导出为 XMind 思维导图
python testcase-generator/scripts/testcase_to_xmind.py "test-case/"
```

#### 测试用例格式（Text Protocol v0.2）

```markdown
## [P0] 用例标题描述
[测试类型] 功能
[前置条件] 用户已登录；账号未锁定
[测试步骤] 1. 打开登录页面。2. 输入用户名test_user。3. 点击登录按钮。
[预期结果] 1. 页面跳转到首页。2. 显示用户信息。
```

**优先级**：P0（核心正向）> P1（基本正向）> P2（核心异常）> P3（边界/低频）

**测试类型（12 种）**：功能、兼容性、易用性、性能、稳定性、安全性、可靠性、效果（AI类）、效果（硬件器件类）、可维护性、可移植性、埋点

### 4. Web 应用测试

使用 Playwright 进行自动化测试：

```bash
# 单服务器模式
python webapp-testing/scripts/with_server.py --server "npm run dev" --port 5173 -- python test.py

# 多服务器模式（后端 + 前端）
python webapp-testing/scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python test.py
```

### 5. 测试工作量评估

基于需求分析测试工作量并生成 Excel 报告：

```bash
python test-effort-estimator/scripts/generate_excel.py
```

### 6. 浏览器自动化

使用 agent-browser 进行浏览器自动化：

```bash
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser click @e1
agent-browser fill @e2 "text"
```

### 7. 蓝湖设计稿分析

通过 MCP Server 读取蓝湖项目：

```bash
# 配置 LANHU_COOKIE 后使用
# lanhu_get_pages - 获取原型页面列表
# lanhu_get_designs - 获取 UI 设计图
# lanhu_get_ai_analyze_page_result - AI 分析原型页面
```

### 8. UI/UX 设计智能

使用 ui-ux-pro-max 进行界面设计决策：

- 选择配色方案、字体配对
- 遵循 99 条 UX 指南
- 应用 50+ 设计风格
- 支持 10 种技术栈

### 9. 文档协作

使用 doc-coauthoring 协作撰写文档：

- PRD、技术规格、提案
- 三阶段工作流：上下文收集 → 迭代优化 → 读者测试

### 10. 主题应用

使用 theme-factory 为幻灯片/文档应用主题：

- 10 种预设主题
- 自定义主题生成

### 11. Excel 处理

使用 xlsx 进行电子表格操作：

```bash
# 公式重算
python xlsx/scripts/recalc.py file.xlsx
```

### 12. PDF 处理

使用 pdf 进行 PDF 操作：

- 读取/提取文本
- 合并/分割
- 表单填写
- 提取图片

### 13. PPT 处理

使用 pptx 进行演示文稿操作：

```bash
# 文本提取
python -m markitdown presentation.pptx

# 缩略图生成
python pptx/scripts/thumbnail.py presentation.pptx
```

### 14. 技能评估与创建

评估和迭代优化技能：

```bash
# 运行评估
python skill-creator/scripts/run_eval.py

# 快速验证
python skill-creator/scripts/quick_validate.py

# 打包技能
python -m skill-creator.scripts.package_skill <path/to/skill-folder>
```

### 15. Prompt 工程

优化和评估 LLM Prompts：

- Zero-shot / Few-shot / Chain-of-thought
- 结构化输出
- 评估框架

### 16. 女娲造人

蒸馏人物思维框架为可运行 Skill：

- 明确人名 → 直接蒸馏
- 模糊需求 → 诊断推荐 → 再蒸馏

## 🏗️ 项目结构

```
qa-skills/
├── agent-browser/              # 浏览器自动化
│   ├── SKILL.md
│   ├── references/             # 认证、命令、性能分析等参考文档
│   └── templates/              # 认证会话、表单自动化等模板
├── analyze-requirements/       # 需求分析全流程编排
│   └── SKILL.md
├── doc-based-testcase-generator/  # 文档驱动用例生成
│   └── SKILL.md
├── doc-coauthoring/            # 文档协作
│   └── SKILL.md
├── huashu-nuwa/                # 女娲造人
│   ├── SKILL.md
│   ├── examples/               # 人物思维框架示例
│   ├── references/
│   └── scripts/
├── lanhu-design/               # 蓝湖设计稿分析
│   └── SKILL.md
├── pdf/                        # PDF 处理
│   ├── SKILL.md
│   ├── scripts/
│   ├── reference.md
│   └── forms.md
├── prompt-engineer/            # Prompt 工程
│   ├── SKILL.md
│   └── references/
├── pptx/                       # PPT 处理
│   ├── SKILL.md
│   ├── scripts/
│   ├── editing.md
│   └── pptxgenjs.md
├── requirements-analysis/      # 对话式需求分析
│   ├── SKILL.md
│   └── references/
├── requirements-analyzer/      # 文档需求提取
│   ├── SKILL.md
│   ├── evals/
│   └── references/
├── skill-creator/              # 技能创建与评估
│   ├── SKILL.md
│   ├── agents/
│   ├── eval-viewer/
│   └── scripts/
├── test-effort-estimator/      # 测试工作量评估
│   ├── SKILL.md
│   └── scripts/
├── testcase-generator/         # 测试用例生成
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── testcase-planner/           # 测试规划
│   ├── SKILL.md
│   └── scripts/
├── theme-factory/              # 主题工厂
│   ├── SKILL.md
│   ├── themes/
│   └── theme-showcase.pdf
├── ui-ux-pro-max/             # UI/UX 设计智能
│   └── SKILL.md
├── webapp-testing/             # Web应用测试
│   ├── SKILL.md
│   ├── examples/
│   └── scripts/
├── xlsx/                       # Excel 处理
│   ├── SKILL.md
│   └── scripts/
├── github-discover/            # GitHub 开源项目发现与每日热榜文章生成
│   ├── SKILL.md
│   ├── evals/
│   ├── references/
│   └── scripts/
├── zentao-bug-submitter/       # 禅道 Bug 自动提交（REST API v1）
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── AGENTS.md                   # Agent 指南
└── CLAUDE.md                   # Claude Code 指南
```

### 技能内部结构

每个技能遵循统一结构：

```
skill-name/
├── SKILL.md           # 必需：技能定义（含 YAML frontmatter）
├── references/        # 可选：按需加载的参考文档
├── scripts/           # 可选：可执行 Python 脚本
├── templates/         # 可选：模板文件
├── assets/            # 可选：资源文件
├── examples/          # 可选：示例代码
└── LICENSE.txt        # 可选：许可证（如有）
```

### 三级加载机制

技能采用渐进式上下文管理：

1. **元数据**（name + description）— 始终在上下文中（~100 词）
2. **SKILL.md 正文** — 技能触发时加载（理想 <500 行）
3. **捆绑资源** — 按需加载（references/、scripts/）

## 🔧 环境变量

| 变量 | 用途 | 所属技能 |
|------|------|----------|
| `LANHU_COOKIE` | 蓝湖平台认证 Cookie | lanhu-design |
| `AGENT_BROWSER_ENCRYPTION_KEY` | 认证保险库加密密钥 | agent-browser |
| `AGENT_BROWSER_HEADED` | 启用可视化浏览器模式 | agent-browser |
| `AGENT_BROWSER_DEFAULT_TIMEOUT` | 默认超时时间 | agent-browser |
| `GITHUB_TOKEN` | GitHub API token（可选，提升限频至 5000次/小时） | github-discover |
| `ZENTAO_URL` | 禅道根地址 | zentao-bug-submitter |
| `ZENTAO_ACCOUNT` | 禅道登录账号 | zentao-bug-submitter |
| `ZENTAO_PASSWORD` | 禅道登录密码 | zentao-bug-submitter |
| `ZENTAO_VERIFY_SSL` | 是否校验 SSL（内网自签名证书设为 0） | zentao-bug-submitter |

## 🛠️ 技术栈

- **语言**：Python 3.10+
- **核心库**：pandas（数据处理）、openpyxl（Excel I/O）、python-docx（Word 文档）、Playwright（浏览器自动化）、pypdf（PDF 处理）
- **浏览器**：Chromium（通过 Playwright）
- **CLI 工具**：agent-browser（Node.js）

## 📝 代码规范

- Python 遵循 PEP8，4 空格缩进，单行最大 120 字符
- 函数/变量 `snake_case`，类 `PascalCase`，常量 `UPPER_SNAKE_CASE`
- 使用类型注解
- 异常捕获指定具体类型，不使用裸 `except`
- 导入顺序：标准库 → 第三方库 → 本地模块

## 📄 License

本项目中的 `skill-creator`、`webapp-testing`、`theme-factory` 等模块包含各自的 LICENSE 文件，请参阅对应目录。
