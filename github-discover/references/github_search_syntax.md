# GitHub Search Syntax 参考

GitHub Search API 支持丰富的查询语法，可用于精确筛选仓库。所有语法同样适用于 Web 界面搜索。

---

## 基本语法

```
GET https://api.github.com/search/repositories?q=<query>&sort=<sort>&order=<order>&per_page=<n>
```

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `q` | 搜索关键词（必填） | 见下方语法 |
| `sort` | 排序字段 | `stars` / `forks` / `help-wanted-issues` / `updated` |
| `order` | 排序方向 | `desc`（默认）/ `asc` |
| `per_page` | 每页数量 | 1–100（默认 30） |
| `page` | 页码 | 从 1 开始 |

---

## 关键词匹配

### 基础匹配

```
# 精确匹配仓库名
q=langchain

# 匹配描述中包含关键词
q=agent framework

# 匹配多个关键词（AND 逻辑）
q=python agent

# OR 逻辑
q=llm OR large-language-model

# 排除词用 - 前缀
q=agent -chatgpt
```

### 位置限定

| 语法 | 说明 | 示例 |
|------|------|------|
| `name:<词>` | 匹配仓库名 | `name:langchain` |
| `user:<用户>` | 匹配所有者 | `user:langchain-ai` |
| `org:<组织>` | 匹配组织 | `org:facebook` |
| `description:<词>` | 匹配描述 | `description:"machine learning"` |
| `topic:<主题>` | 匹配标签 | `topic:llm` |
| `language:<语言>` | 匹配主要语言 | `language:python` |
| `license:<spdx-id>` | 匹配许可证 | `license:mit` |
| `size:<bytes>` | 匹配仓库大小 | `size:>10000` |

---

## 范围运算符

支持 `>`, `<`, `>=`, `<=`, `=`

| 语法 | 说明 | 示例 |
|------|------|------|
| `stars:>1000` | Stars 大于 1000 | `stars:>=10000` |
| `forks:<500` | Forks 少于 500 | `forks:>100` |
| `created:<2024-01-01` | 创建时间在 2024 之前 | — |
| `updated:>2025-09-01` | 最近更新在 2025-09-01 之后 | — |
| `pushed:>2026-01-01` | 最近推送到 2026 之后 | — |

时间格式：`YYYY-MM-DD`，也支持相对语法 `>1y`（一年前）、`>6m`（半年前）、`>30d`（30天前）。

---

## 组合查询示例

### 按热度找项目

```
# Python 语言，Stars>5000，按星标排序
q=python+framework&sort=stars&order=desc&language=python

# 近期活跃（近7天有更新），按星标排序
q=created:>2026-08-28&sort=stars&order=desc
```

### 按活跃度筛选

```
# 近一年有更新，至少 1000 stars
q=stars:>=1000&sort=updated&order=desc

# 最近提交在 30 天内
q=pushed:>2026-08-06&sort=stars
```

### 按许可证筛选

```
# MIT 许可证的 AI 项目
q=ai+agent&license:mit&sort=stars

# 允许商用的项目（mit 或 apache-2.0）
q=tool&license:mit OR license:apache-2.0
```

### 项目规模筛选

```
# 小型项目（< 1MB），适合快速学习
q=rust&size:<1024&sort=stars

# 大型项目（> 50MB），通常是成熟框架
q=framework&size:>51200&sort=stars
```

### 按贡献者数量

```
# 有多人维护的项目（更可靠）
q=agent&contributors:>10&sort=stars
```

---

## 高级语法

### 通配符

```
# 仓库名以 langchain 开头
q=langchain*

# 描述包含 agent 但不包含 chat
q=agent -chat
```

### 短语匹配（引号内空格保留）

```
# 精确短语
q="machine learning"
q="react dashboard"
```

### 逻辑运算优先级

```
# AND 优先于 OR
q=python agent OR rust framework
# 等价于：q=(python AND agent) OR (rust AND framework)

# 用括号显式分组
q=(python OR rust) AND agent
```

---

## 常用搜索模板

### 热门 AI/LLM 项目

```
q=large-language-model OR llm OR agent&sort=stars&order=desc&per_page=20
```

### 新出现的热门项目（近7天）

```
q=created:>2026-08-28&sort=stars&order=desc&per_page=20
```

### 活跃的开源框架（多人维护）

```
q=framework&contributors:>5&stars:>=1000&sort=stars&order=desc
```

### 学习友好型项目（中小型，活跃）

```
q=python&size:<20480&stars:>=500&updated:>2026-06-01&sort=stars
```

### 特定技术栈组合

```
# Rust + async + web
q=rust+async+web+framework&sort=stars

# TypeScript + testing
q=typescript+testing+framework&sort=stars
```

---

## API 调用示例

```bash
# 搜索
python scripts/github_api.py search "python llm agent" --sort stars --lang python --per-page 10

# 按时间筛选热门
python scripts/github_api.py trends --since weekly

# 查单个仓库
python scripts/github_api.py repo "langchain-ai/langchain"
```

---

## 注意事项

1. **URL 编码**：查询中的空格、特殊字符需 URL 编码（脚本已自动处理）
2. **限频**：无 token 60次/小时，有 token 5000次/小时；频繁查询先检查缓存
3. **搜索结果不计入 stars**：`total_count` 是估算值，超过 1000 万时不准确
4. **API 只返回公开仓库**：私有仓库不在搜索结果中
5. **`language` 过滤器**：GitHub 按主要语言归类，一个仓库只能有一个 primary language
