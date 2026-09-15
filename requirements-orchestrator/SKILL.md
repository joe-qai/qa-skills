---
name: requirements-orchestrator
description: |
  需求分析全流程编排。根据输入类型自动调度 Agent 获取数据，输出结构化需求报告和开发任务清单。

  触发场景：
  - 收到 Axure 原型截图需要分析需求
  - 需要将产品需求转化为开发任务
  - 云效任务需要拆解为开发步骤
  - 需求评审前需要结构化分析

  触发词：分析需求、需求分析、原型分析、需求拆解、分析原型图
---

# 需求分析全流程

## 核心原则

**先判断复杂度，简单需求直接分析，复杂需求走 Agent 编排。分析完成后推荐开发流程。**

## 步骤 0：复杂度判断（必须先做）

```
用户提供需求线索
  │
  ├─ 简单需求？ ──→ 快速路径（直接分析输出任务清单）
  │   - 纯文字描述，功能明确
  │   - 单表 CRUD，无需看原型图
  │   - 用户已给出完整字段列表
  │
  └─ 复杂需求？ ──→ Agent 路径（启动 doc-requirements-extractor）
      - 提供了 Axure 原型截图
      - 提供了云效任务编号
      - 多页面/多模块联动
      - 业务流程复杂，需要状态流转设计
```

## 快速路径（简单需求）

```
理解需求 → 设计表结构 → 列出接口清单 → 输出任务清单 → 推荐 /crud 或 /dev
```

不启动 Agent，直接在主对话中完成。输出格式参考下方"输出规范"。

## Agent 路径（复杂需求）

```
步骤 1：收集信息（从用户消息中提取）
  - Axure 原型截图路径
  - 云效任务编号
  - 需求描述文字
  - 关联模块信息

步骤 2：启动 doc-requirements-extractor Agent
  └── doc-requirements-extractor(Opus) 内部自动编排：
      ├── image-reader(Haiku) × N张 → 提取原型图结构（有截图时）
      ├── task-fetcher(Haiku) → 获取云效任务详情（有任务号时）
      └── 汇总分析 → 输出需求报告 + 任务清单

步骤 3：Opus 主会话接收报告 → 推荐开发流程
```

## Agent 启动规则

### 按信息量决定启动方式

| 用户提供的信息 | 启动方式 |
|---------------|---------|
| 只有文字描述 | 快速路径（不启动 Agent） |
| 文字 + 原型截图 | doc-requirements-extractor → 内部调 image-reader |
| 文字 + 云效任务号 | doc-requirements-extractor → 内部调 task-fetcher |
| 原型截图 + 云效任务号 | doc-requirements-extractor → 内部并行调 image-reader + task-fetcher |

### 启动示例

```
# 有原型截图
Agent(subagent_type="doc-requirements-extractor",
  prompt="分析以下 Axure 原型截图，输出需求分析报告和开发任务清单：
  截图路径：/path/to/image1.png, /path/to/image2.png
  需求描述：xxx")

# 有云效任务
Agent(subagent_type="doc-requirements-extractor",
  prompt="获取云效任务 SARW-456 的详情，结合以下需求描述分析：xxx")
```

## 输出规范

无论走快速路径还是 Agent 路径，最终输出必须包含：

1. **业务概述** — 一段话描述需求
2. **数据库设计** — 建表 SQL（遵循项目规范）
3. **接口清单** — 路由 + 方法 + 说明
4. **开发任务拆解** — 按依赖排序的任务列表
5. **推荐开发流程** — 根据复杂度推荐

### 复杂度 → 开发流程推荐

| 复杂度 | 推荐流程 |
|--------|---------|
| 轻量（单表 CRUD） | `/crud` 生成 + `/dev` 补充 |
| 中等（2-3 表联动） | `/dev` 按任务逐步开发 |
| 复杂（多模块协作） | OpenSpec `/opsx:new` → `/opsx:ff` → `/opsx:apply` |

## 注意

- 简单需求不要过度编排，直接分析就行
- 与 `bug-detective` / `fix-bug` 的区别：本技能面向**新功能开发前的需求分析**，不涉及 Bug 排查
- 数据库设计必须遵循项目规范（雪花 ID、审计字段、del_flag=2 正常）
- 如果需求信息不完整，主动列出需要确认的点，而不是猜测
