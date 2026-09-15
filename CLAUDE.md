# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI Agent Testing Skills Collection** (测试技能集合) for iFlow CLI, containing 19 specialized skills that automate the software testing lifecycle—from requirements analysis to test execution.

**Key Documentation**: [AGENTS.md](AGENTS.md) contains complete skill descriptions, workflows, and usage examples.

## Skill Inventory (19 Skills)

| Skill | Purpose | Key Scripts/Resources |
|-------|---------|----------------------|
| `doc-requirements-extractor` | Extract requirements from Excel/PDF/PNG/Word/TXT | references/ |
| `dialog-requirements-refiner` | Conversational requirements, EPIC decomposition | references/ |
| `requirements-orchestrator` | Full requirements orchestration (Agent dispatch) | — |
| `testcase-planner` | Test planning (ITEM/POINT hierarchy) | parse_plan.py |
| `testcase-generator` | Generate test cases (Markdown/Excel/XMind) | validate.py, to_excel.py, testcase_to_xmind.py |
| `doc-based-testcase-generator` | Generate cases from PRD/interface docs | — |
| `test-effort-estimator` | Test effort estimation + Excel report | generate_excel.py |
| `webapp-testing` | Playwright-based web testing | with_server.py |
| `agent-browser` | Browser automation CLI | npx agent-browser |
| `lanhu-design` | Lanhu/Axure prototype analysis | MCP Server |
| `skill-creator` | Create and evaluate skills | run_eval.py, aggregate_benchmark.py |
| `ui-ux-pro-max` | UI/UX design intelligence | 50+ styles, 161 palettes |
| `theme-factory` | Apply themes to slides/docs | 10 preset themes |
| `doc-coauthoring` | Documentation collaboration | — |
| `huashu-nuwa` | Distill thinking frameworks into Skills | examples/ |
| `prompt-engineer` | Prompt engineering and optimization | references/ |
| `xlsx` | Excel processing | recalc.py |
| `pdf` | PDF processing | pypdf, pdfplumber |
| `pptx` | PPT processing | thumbnail.py, markitdown |

## Common Development Commands

### Python Environment

```bash
# Install dependencies
pip install pandas openpyxl python-docx playwright pypdf pdfplumber

# Install Playwright browsers
playwright install chromium

# Verify installation
python -c "import pandas, openpyxl, docx, playwright"
```

### Test Case Generation Workflow

```bash
# Validate test case format (single file)
python testcase-generator/scripts/validate.py --single "test-case/{ITEM}/{POINT}.md"

# Validate entire directory
python testcase-generator/scripts/validate.py "test-case/"

# Check for duplicates
python testcase-generator/scripts/validate.py "test-case/" --check-duplicates

# Export to Excel
python testcase-generator/scripts/to_excel.py "test-case/" -o "test-case/export.xlsx"

# Export to XMind
python testcase-generator/scripts/testcase_to_xmind.py "test-case/"
```

### Web Application Testing

```bash
# Run tests with server lifecycle management
python webapp-testing/scripts/with_server.py --server "npm run dev" --port 5173 -- python your_test.py

# Multiple servers (backend + frontend)
python webapp-testing/scripts/with_server.py \
  --server "cd backend && python server.py" --port 3000 \
  --server "cd frontend && npm run dev" --port 5173 \
  -- python your_test.py
```

### Browser Automation

```bash
agent-browser open https://example.com
agent-browser snapshot -i
agent-browser click @e1
agent-browser fill @e2 "text"
```

### Skill Evaluation (skill-creator)

```bash
# Run evaluation
python skill-creator/scripts/run_eval.py

# Aggregate benchmark results
python -m skill-creator.scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>

# Generate eval viewer report
python skill-creator/eval-viewer/generate_review.py <workspace>/iteration-N --skill-name "my-skill"

# Package skill
python -m skill-creator.scripts.package_skill <path/to/skill-folder>
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

## High-Level Architecture

### Skill Organization

Each skill follows a consistent structure:

```
skill-name/
├── SKILL.md              # Required: Skill definition with YAML frontmatter
├── references/           # Optional: Documentation loaded on demand
├── scripts/              # Optional: Executable Python scripts
├── templates/            # Optional: Template files
├── assets/               # Optional: Resources (icons, fonts)
├── examples/             # Optional: Example code
└── LICENSE.txt          # Optional: License file
```

**SKILL.md Frontmatter**:
```yaml
---
name: skill-name
description: When to trigger and what it does
allowed-tools: Read, Write, Bash  # Optional
---
```

### Three-Level Loading System

Skills use progressive disclosure to manage context:

1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - Loaded when skill triggers (<500 lines ideal)
3. **Bundled resources** - Loaded as needed (references/, scripts/)

### Key Skills and Their Roles

| Skill | Purpose | Key Scripts |
|-------|---------|------------|
| `testcase-generator` | Generate structured test cases from test points | `validate.py`, `to_excel.py`, `testcase_to_xmind.py` |
| `testcase-planner` | Create test plans (ITEM → POINT hierarchy) | `parse_plan.py` |
| `doc-requirements-extractor` | Extract requirements from Excel/PDF/PNG/Word | — |
| `requirements-orchestrator` | Orchestrate full requirements analysis workflow | — |
| `agent-browser` | Browser automation via CLI | Uses `npx agent-browser` |
| `webapp-testing` | Playwright-based web app testing | `with_server.py` |
| `skill-creator` | Create and evaluate new skills | `run_eval.py`, `aggregate_benchmark.py` |
| `test-effort-estimator` | Estimate testing effort | `generate_excel.py` |
| `lanhu-design` | Analyze Lanhu/Axure prototypes | Uses lanhu MCP Server |
| `ui-ux-pro-max` | UI/UX design intelligence | 50+ styles, 161 palettes |
| `theme-factory` | Theme application for slides/docs | 10 preset themes |
| `doc-coauthoring` | Documentation collaboration | — |
| `huashu-nuwa` | Distill thinking frameworks | examples/ |
| `prompt-engineer` | Prompt optimization | references/ |
| `xlsx` | Excel operations | recalc.py |
| `pdf` | PDF operations | pypdf |
| `pptx` | PPT operations | thumbnail.py |

### Test Case Format (Text Protocol v0.2)

Test cases follow a strict Markdown format:

```markdown
## [P0] Test case title
[Test type] Function
[Precondition] User logged in
[Steps] 1. Open page. 2. Click button.
[Expected] 1. Show success message.
```

**Priority**: P0 (core positive), P1 (basic positive), P2 (core exception), P3 (boundary/low frequency)

**Test Types (12 enum values)**: 功能, 兼容性, 易用性, 性能, 稳定性, 安全性, 可靠性, 效果（AI类）, 效果（硬件器件类）, 可维护性, 可移植性, 埋点

### Complete Testing Workflow

```
1. Requirements → 2. Test Planning → 3. Test Case Gen → 4. Execution → 5. Reporting

doc-requirements-extractor/      testcase-planner/      testcase-generator/     webapp-testing/
requirements-orchestrator/                              scripts/validate.py
                                                   scripts/to_excel.py
                                                   scripts/testcase_to_xmind.py
```

### Complete Skill Categories

**Testing Skills (Core)**:
- doc-requirements-extractor, dialog-requirements-refiner, requirements-orchestrator
- testcase-planner, testcase-generator, doc-based-testcase-generator
- test-effort-estimator, webapp-testing

**Design & Documentation Skills**:
- lanhu-design, ui-ux-pro-max, theme-factory
- doc-coauthoring, prompt-engineer

**Platform & Engineering Skills**:
- agent-browser, skill-creator

**File Processing Skills**:
- xlsx, pdf, pptx

**Advanced Skills**:
- huashu-nuwa (人物思维蒸馏)

## Working with Scripts

**Important**: Scripts in `scripts/` directories are designed to be used as black-box utilities. Always run with `--help` first rather than reading the source:

```bash
python <skill>/scripts/<script>.py --help
```

This keeps the context window clean—these scripts handle complex workflows reliably without needing to be understood in detail.

## Dependencies

- **Python**: 3.10+
- **Core Libraries**: pandas (Excel), openpyxl (Excel I/O), python-docx (Word), playwright (browser automation), pypdf (PDF), pdfplumber (PDF tables)
- **Browser**: Chromium (via Playwright)
- **CLI Tools**: agent-browser (Node.js)

## Environment Variables

### agent-browser
- `AGENT_BROWSER_ENCRYPTION_KEY` - Encryption key for auth vault
- `AGENT_BROWSER_HEADED` - Enable visual browser mode
- `AGENT_BROWSER_DEFAULT_TIMEOUT` - Default timeout

### lanhu-design (Lanhu MCP Server)
- `LANHU_COOKIE` - Blue Lake platform authentication (configured in `.claude/settings.json`)
