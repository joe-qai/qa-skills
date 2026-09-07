# AGENTS.md - Testing Skills Collection

## Project Overview

AI Agent Testing Skills Collection for iFlow CLI. 29 skills for software testing lifecycle.

**Tech Stack**: Python 3.10+, Playwright, pandas, openpyxl, python-docx, pypdf

---

## Skill Inventory (29 Skills)

| Skill | Purpose | Commands/Resources |
|-------|---------|-------------------|
| `requirements-analyzer` | Extract requirements from Excel/PDF/PNG/Word/TXT | references/ |
| `requirements-analysis` | Conversational requirements, EPIC decomposition | references/ |
| `analyze-requirements` | Full requirements orchestration (Agent dispatch) | — |
| `testcase-planner` | Test planning (ITEM/POINT hierarchy) | parse_plan.py |
| `testcase-generator` | Generate test cases (Markdown/Excel/XMind) | validate.py, to_excel.py |
| `doc-based-testcase-generator` | Generate cases from PRD/interface docs | — |
| `test-effort-estimator` | Test effort estimation + Excel report | generate_excel.py |
| `webapp-testing` | Playwright-based web testing | with_server.py |
| `agent-browser` | Browser automation CLI | npx agent-browser |
| `lanhu-design` | Lanhu/Axure prototype analysis | MCP Server |
| `skill-creator` | Create and evaluate skills | run_eval.py, quick_validate.py |
| `ui-ux-pro-max` | UI/UX design intelligence | 50+ styles, 161 palettes |
| `theme-factory` | Apply themes to slides/docs | 10 preset themes |
| `doc-coauthoring` | Documentation collaboration | — |
| `huashu-nuwa` | Distill thinking frameworks into Skills | examples/ |
| `prompt-engineer` | Prompt engineering and optimization | references/ |
| `xlsx` | Excel processing | recalc.py |
| `pdf` | PDF processing | pypdf, pdfplumber |
| `pptx` | PPT processing | thumbnail.py, markitdown |
| `github-discover` | GitHub search + daily trending repo → blog post generator | github_api.py, daily_discover.py |
| `zentao-bug-submitter` | 禅道 Bug 自动提交（REST API v1） | zentao_client.py |
| `browser-use` | CDP 浏览器自动化（爬取/测试/截图/交互） | browser-use CLI |
| `ai-agent-testing` | AI Agent 行为/规划/安全边界测试 | prompts/ |
| `prompt-testing` | Prompt 质量评估与边界测试 | prompts/ |
| `prompt-injection-testing` | Prompt 注入攻击检测与安全测试 | prompts/ |
| `performance-test-jmeter` | JMeter 性能测试方案与报告 | performance-test-jmeter.md |
| `capacity-planning-analysis` | 容量规划与瓶颈分析 | capacity-planning-analysis.md |
| `mobile-testing` | 移动端功能与兼容性测试 | mobile-testing.md, convert_*.py |
| `security-testing` | 安全扫描与渗透测试流程 | security-testing.md, run-scan.sh |

---

## Build/Lint/Test Commands

### Setup
```bash
pip install pandas openpyxl python-docx playwright pypdf pdfplumber
playwright install chromium
```

### Validation (Test Suite)
```bash
# Validate single test case
python testcase-generator/scripts/validate.py --single "test-case/ITEM/POINT.md"

# Validate entire directory
python testcase-generator/scripts/validate.py "test-case/"

# Check duplicates
python testcase-generator/scripts/validate.py "test-case/" --check-duplicates
```

### Export Commands
```bash
# To Excel
python testcase-generator/scripts/to_excel.py "test-case/" -o "export.xlsx"

# To XMind
python testcase-generator/scripts/testcase_to_xmind.py "test-case/"

# Effort estimation
python test-effort-estimator/scripts/generate_excel.py
```

### Skill Evaluation
```bash
python skill-creator/scripts/run_eval.py
python skill-creator/scripts/quick_validate.py
```

### Web Testing
```bash
python webapp-testing/scripts/with_server.py --server "npm run dev" --port 5173 -- python test.py
```

### Browser Automation
```bash
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser click @e1
agent-browser fill @e2 "text"
```

### Excel Processing
```bash
python xlsx/scripts/recalc.py file.xlsx
```

### PPT Processing
```bash
python -m markitdown presentation.pptx
python pptx/scripts/thumbnail.py presentation.pptx
```

---

## Code Style Guidelines

### Python

**Imports**: Standard → third-party → local, blank lines between groups
```python
import os
import sys

import pandas as pd
from openpyxl import Workbook

from . import local_module
```

**Formatting**: 4 spaces, max 120 chars per line
```python
# Good
result = func(arg1, arg2,
              arg3=default)

# Bad
result = func(arg1, arg2, arg3=default)
```

**Types**: Use type hints for function signatures
```python
def process(path: str) -> dict[str, Any]:
    ...
```

**Naming**:
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Error Handling**: Always catch specific exceptions
```python
try:
    result = risky()
except ValueError as e:
    logger.error(f"Invalid: {e}")
    raise
```

### SKILL.md Format

Required YAML frontmatter:
```yaml
---
name: skill-name
description: When to trigger and what it does
---
```

### Test Case Format (v0.2)

```markdown
## [P0] Test case title
[Test type] Function
[Precondition] User logged in
[Steps] 1. Open page. 2. Click button.
[Expected] 1. Show success message.
```

**Priority**: P0 > P1 > P2 > P3

**Test Types (12)**: 功能, 兼容性, 易用性, 性能, 稳定性, 安全性, 可靠性, 效果(AI类), 效果(硬件器件类), 可维护性, 可移植性, 埋点

---

## Directory Structure

```
skill-name/
├── SKILL.md           # Required: definition + YAML frontmatter
├── references/        # Optional: documentation
├── scripts/           # Optional: Python utilities
├── templates/         # Optional: templates
├── assets/            # Optional: resources
├── examples/          # Optional: examples
└── LICENSE.txt        # Optional: license file
```

---

## Complete Workflow

```
Requirements → Test Planning → Case Gen → Execution
(requirements-analyzer) (testcase-planner) (testcase-generator) (webapp-testing)
```

### Testing Skills (Core)

```
requirements-analyzer/      testcase-planner/      testcase-generator/
analyze-requirements/       └── parse_plan.py      ├── validate.py
                                                      to_excel.py
                                                      testcase_to_xmind.py
```

### Design & Documentation Skills

```
lanhu-design/               ui-ux-pro-max/         doc-coauthoring/
MCP Server                  50+ styles             PRD/提案/设计文档
                             161 palettes

theme-factory/              pptx/                  pdf/
10 preset themes            thumbnail.py            pypdf
                              markitdown
```

### Platform & Engineering Skills

```
agent-browser/              webapp-testing/         skill-creator/
npx agent-browser           with_server.py          run_eval.py
                                                       quick_validate.py

github-discover/
GitHub 搜索 + 每日热榜文章生成

browser-use/
CDP 浏览器自动化（爬取/截图/表单交互/测试）
```

---

## Environment Variables

- `LANHU_COOKIE`: Blue Lake auth (`.claude/settings.json`)
- `AGENT_BROWSER_ENCRYPTION_KEY`: Auth vault encryption key
- `AGENT_BROWSER_HEADED`: Enable visual browser mode
- `AGENT_BROWSER_DEFAULT_TIMEOUT`: Default timeout
- `GITHUB_TOKEN`: GitHub API token（可选，提升限频至 5000次/小时）
- `ZENTAO_URL`: 禅道根地址（如 `https://<host>/zentao`）
- `ZENTAO_ACCOUNT`: 禅道登录账号
- `ZENTAO_PASSWORD`: 禅道登录密码
- `ZENTAO_VERIFY_SSL`: 可选，设为 `0` 不校验 SSL 证书（内网自签名证书场景）
- `BROWSER_USE_API_KEY`: Browser Use Cloud API key（可选，远程浏览器）
- `BH_DOMAIN_SKILLS`: 启用域名级技能（`1`）
- `BH_AGENT_WORKSPACE`: 自定义工作区路径

---

**Last Updated**: 2026-09-05
