---
name: theme-factory
description: Toolkit for styling artifacts with a theme. Use when the user wants to apply a consistent visual theme to slides, docs, reports, or HTML pages; includes 10 pre-set themes with hex colors/fonts, or generate a custom theme on-the-fly.
---

# Theme Factory

## 何时使用

- 用户需要为幻灯片、文档、报告、HTML 页面应用统一的视觉主题。
- 需要从 10 个预设主题中选择，或生成自定义主题。

## 输入要求

| 必填 | 字段 | 说明 |
|------|------|------|
| ✅ | 目标产物 | 幻灯片 / 文档 / 报告 / HTML 页面 |
| ✅ | 主题选择 | 从预设选择（指定名称）或描述自定义需求 |
| ⬜ | 产物文件 | 已有的 .pptx / .md / .html 文件路径 |
| ⬜ | 品牌要求 | 特定颜色、字体、风格约束 |

## 预设主题

| # | 主题 | 主色 | 强调色 | 背景 | 字体 | 适用场景 |
|---|------|------|--------|------|------|---------|
| 1 | Ocean Depths | `#1a2332` | `#2d8b8b` | `#f1faee` | DejaVu Sans | 企业、金融、咨询 |
| 2 | Sunset Boulevard | `#e76f51` | `#f4a261` | `#264653` | DejaVu Serif | 创意、营销、活动 |
| 3 | Forest Canopy | `#2d6a4f` | `#52b788` | `#f0f7f0` | DejaVu Sans | 自然、健康、可持续 |
| 4 | Modern Minimalist | `#36454f` | `#708090` | `#ffffff` | DejaVu Sans | 科技、架构、数据 |
| 5 | Golden Hour | `#b8860b` | `#daa520` | `#fdf5e6` | DejaVu Serif | 奢华、温暖、秋季 |
| 6 | Arctic Frost | `#4682b4` | `#87ceeb` | `#f0f8ff` | DejaVu Sans | 冬季、洁净、医疗 |
| 7 | Desert Rose | `#bc8f8f` | `#d4a0a0` | `#fff5ee` | DejaVu Sans | 优雅、柔和 |
| 8 | Tech Innovation | `#0066ff` | `#00ffff` | `#1e1e1e` | DejaVu Sans | 创业、AI/ML、数字 |
| 9 | Botanical Garden | `#228b22` | `#90ee90` | `#f5fff5` | DejaVu Sans | 有机、清新、自然 |
| 10 | Midnight Galaxy | `#191970` | `#4b0082` | `#0a0a2e` | DejaVu Sans | 戏剧、宇宙、夜景 |

## 执行流程

### 1. 主题选择

- 用户指定预设名称 → 直接使用
- 用户描述需求（如"科技感"、"温暖"）→ 匹配最接近的预设
- 用户提供品牌色 → 基于品牌色生成自定义主题

### 2. 主题应用

读取 `themes/<theme-name>.md` 获取完整色值和字体，应用到目标产物：

| 产物类型 | 应用方式 |
|----------|---------|
| .pptx 幻灯片 | 修改母版/布局的颜色方案和字体 |
| .md 文档 | 生成带主题样式的 HTML 版本 |
| .html 页面 | 应用 CSS 变量（颜色、字体、间距） |
| 报告 | 按主题配色生成图表和排版 |

### 3. 质量校验

应用后执行以下校验：

- [ ] 所有颜色使用主题色值（无随意配色）
- [ ] 标题和正文使用主题指定字体
- [ ] 背景色与文字色对比度 ≥ 4.5:1（可读性）
- [ ] 强调色仅用于关键元素（标题、按钮、高亮），不超过 20% 面积
- [ ] 整体风格一致（无混搭不同主题的元素）

### 4. 输出交付物

| 文件 | 内容 |
|------|------|
| `theme.md` | 主题规范（色值、字体、使用规则） |
| 应用后的产物文件 | 已应用主题的 .pptx / .html / 报告 |

## 核心约束

- 先展示主题预览（theme-showcase.pdf），等用户确认后再应用。
- 不修改用户未指定的布局结构，只改颜色和字体。
- 自定义主题需要用户确认色值后再应用。
- 确保对比度满足可读性要求。

## 常见误区

- 不经确认直接应用 → 必须先展示预览。
- 混搭不同主题的元素 → 一个产物只用一个主题。
- 忽略可读性 → 浅色背景用深色文字，反之亦然。
