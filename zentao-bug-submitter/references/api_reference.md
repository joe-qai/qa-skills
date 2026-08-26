# 禅道 REST API v1 参考手册

> 适用于禅道企业版 / 旗舰版 / 开源版 12.x+。Base URL: `https://<host>/zentao/api.php/v1`

## 目录
1. [认证](#认证)
2. [产品](#产品)
3. [模块](#模块)
4. [版本 Build](#版本-build)
5. [用户](#用户)
6. [附件上传](#附件上传)
7. [创建 Bug](#创建-bug)
8. [字段枚举值](#字段枚举值)
9. [常见问题](#常见问题)

---

## 认证

### 获取 Token
```
POST /tokens
Content-Type: application/json

{
  "account": "<账号>",
  "password": "<密码>"
}
```

**响应：**
```json
{ "token": "ar10jprf375l1r9af67fxxxxxx" }
```

### 使用 Token
后续所有请求在 Header 中携带：
```
Token: <token_value>
```

> Token 有有效期，过期后需重新登录获取。脚本中每次操作前自动检查并重新登录。

---

## 产品

### 获取产品列表
```
GET /products?limit=100
```

**响应关键字段：**
```json
{
  "products": [
    { "id": "1", "name": "鹿客智能锁", "code": "lock", "status": "normal" }
  ],
  "page": 1, "total": 10
}
```

---

## 模块

### 获取产品模块树
```
GET /modules?type=bug&id=<product_id>
```

- `type`: 模块类型，提交 Bug 时用 `bug`，其他可选 `case`/`task`/`story`
- `id`: 产品 ID

**响应：** 返回嵌套的模块树，每个节点含 `id`、`name`、`children`。

> 模块 ID 是创建 Bug 时 `module` 字段的值。如果不需要指定模块，可传 `0` 或不传。

---

## 版本 Build

### 获取版本列表
```
GET /builds?project=<project_id>&limit=100
```

> **注意**：部分禅道实例需要通过 `project` 参数查询，而非 `type=product&param=<product_id>`。
> 可从产品详情中获取对应的 project id。
> **部分账号**可能无项目浏览权限（builds 查询返回 403），此时请直接使用版本号字符串创建 Bug。

**响应关键字段：**
```json
{
  "builds": [
    { "id": "3", "name": "V2.5.0", "product": "1", "branch": "0" }
  ]
}
```

> 创建 Bug 时 `openedBuild` 字段传版本 ID（数组形式，如 `[3]` 或 `[3, 5]`）。
> **openedBuild 不可为 0**，必须传有效版本 ID，否则返回 `{"error":{"openedBuild":["「影响版本」不能为空。"]}}`。

---

## 用户

### 获取用户列表
```
GET /users?limit=200
```

**响应关键字段：**
```json
{
  "users": [
    { "account": "zhangsan", "realname": "张三", "email": "zhangsan@example.com" }
  ]
}
```

> 创建 Bug 时 `assignedTo` 字段传用户的 `account`（不是 realname）。

---

## 附件上传

### 上传文件（REST API，推荐）
```
POST /files
Content-Type: multipart/form-data
Token: <token>

uid: <唯一关联标识>
file: <二进制文件>
```

**响应：**
```json
{ "id": "123", "url": "/zentao/file-read-123.html" }
```

### 附件关联机制
禅道通过 `uid` 将上传的文件与后续创建的 Bug 关联：
1. 上传一个或多个文件时，全部使用**同一个** `uid`
2. 创建 Bug 时，在请求体中传入相同的 `uid`
3. 系统自动将该 uid 下的所有文件关联到新创建的 Bug

`uid` 可以是任意字符串，建议使用 UUID。

### 上传兜底策略（`add_or_upload_attachments`）
脚本对附件上传做了两级 REST 兜底，均在失败时不阻断建单：

| 通道 | 方式 | 触发条件 |
|------|------|----------|
| REST A | `POST /files`（field `file`，multipart，带 uid） | 默认第一优先 |
| REST B | `POST /attachments`（objectType/objectID，直接关联到已建 Bug） | 通道 A 返回错误时回退 |

> **注意**：部分禅道实例的 `/api.php/v1/files` 接口存在服务端问题，POST 请求始终返回 `{"error":"error"}`；
> 若通道 A 失败，脚本自动回退到通道 B。若两条 REST 通道均失败，脚本会把附件路径写进 steps，
> 并在返回 JSON 的 `_attachments` 字段中逐文件标注 `ok/channel/message`，后续通过 Web 界面手动关联。

---

## 创建 Bug

### 接口
```
POST /products/<product_id>/bugs
Content-Type: application/json
Token: <token>
```

也可使用：
```
POST /bugs
```
（需在 body 中额外传 `product` 字段）

### 请求字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | **是** | Bug 标题 |
| `severity` | int | **是** | 严重程度 1-5（1最严重） |
| `pri` | int | **是** | 优先级 1-5（1最高） |
| `type` | string | **是** | Bug 类型，见[枚举值](#bug-类型) |
| `openedBuild` | array | **是** | 影响版本 ID 列表，如 `[3]`；支持字符串版本名（如 `["APP_601_28"]`、`["601_28"]`）。若输入模糊，脚本会自动从已有 Bug 中模糊匹配最接近的版本名。传入 `execution` 可确保版本名正确解析。 |
| `steps` | string | **是** | 重现步骤（plain text 格式） |
| `module` | int | 否 | 所属模块 ID |
| `assignedTo` | string | 否 | 当前指派（用户 account） |
| `project` | int | 否 | 所属项目 ID |
| `execution` | int | 否 | 所属执行 ID |
| `os` | string | 否 | 操作系统，如 "Windows 11" |
| `browser` | string | 否 | 浏览器，如 "Chrome 120" |
| `keywords` | string | 否 | 关键词 |
| `mailto` | string | 否 | 抄送人（用户 account，逗号分隔） |
| `deadline` | string | 否 | 截止日期，如 "2026-09-01" |
| `uid` | string | 否 | 附件关联标识 |
| `story` | int | 否 | 关联需求 ID |
| `task` | int | 否 | 关联任务 ID |
| `case` | int | 否 | 关联用例 ID |
| `caseVersion` | int | 否 | 用例版本 |

### steps 字段格式
`steps` 使用 **plain text** 格式（非 HTML），各板块用 `\n\n` 分隔，板块名称用中文方括号标注：

```
【前置条件】
  描述前置条件

【测试步骤】
  1. 第一步操作
  2. 第二步操作
  3. 第三步操作

【实际结果】
  描述实际异常

【预期结果】
  描述预期行为
```

> 如果用户没有提供前置条件，可省略该板块。日志内容可附加在【实际结果】中。
> 每个板块名称后换行，内容前可缩进两个空格。

### 响应
```json
{
  "id": "1024",
  "title": "登录页面崩溃",
  "status": "active",
  ...
}
```

创建成功后，Bug 访问地址为：
```
https://<host>/zentao/bug-view-<bug_id>.html
```

---

## 字段枚举值

### 严重程度 (severity)
| 值 | 含义 |
|----|------|
| 1 | 致命（系统崩溃、数据丢失、核心功能不可用）→ UI 显示 P1 |
| 2 | 严重（主要功能异常）→ 部分实例跳过此值 |
| 3 | 一般（功能异常但有替代方案）→ UI 显示 P2 |
| 4 | 轻微（界面/文案问题、不影响功能）→ UI 显示 P3 |
| 5 | 建议（优化建议、体验改进）→ UI 显示 P4 |

> **注意**：不同禅道实例的严重度标签映射可能不同。部分实例（如家用601）使用 `1→P1, 3→P2, 4→P3`，跳过 2。创建前请从已有 Bug 中确认实际映射关系。

### 优先级 (pri)
| 值 | 含义 |
|----|------|
| 1 | 最高（立即修复） |
| 2 | 高（本迭代修复） |
| 3 | 中（正常排期）→ UI 显示 P2 |
| 4 | 低（有空再修） |
| 5 | 最低（可延后） |

> **注意**：优先级标签映射因实例而异，家用601 实例使用 `1→P1, 3→P2`，跳过 2。创建前请从已有 Bug 中确认。

### Bug 类型 (type)
| 值 | 含义 |
|----|------|
| `codeerror` | 代码错误 |
| `config` | 配置相关 |
| `install` | 安装部署 |
| `security` | 安全相关 |
| `performance` | 性能问题 |
| `standard` | 标准规范 |
| `automation` | 测试脚本 |
| `designdefect` | 设计缺陷 |
| `others` | 其他 |

### 操作系统 (os) 常用值
`Windows 11` / `Windows 10` / `macOS` / `iOS` / `Android` / `Linux` / `ChromeOS` / `其他`

### 浏览器 (browser) 常用值
`Chrome` / `Firefox` / `Safari` / `Edge` / `IE` / `Opera` / `其他`

---

## 常见问题

### 1. 登录返回 401 或无 token
- 检查账号密码是否正确
- 确认该账号有 API 访问权限（禅道后台 → 人员 → 权限）
- 企业版可能需要在后台开启 REST API

### 2. 创建 Bug 提示字段必填
- 不同禅道版本/后台配置可能有不同的必填字段
- 检查返回的错误信息，补充对应字段
- 常见额外必填：`module`（模块）、`project`（项目）
- **openedBuild 不可为 0**，必须传有效版本 ID

### 3. 附件上传返回 `{"error":"error"}`
- 这是禅道服务端问题，非客户端问题
- 脚本会自动切换到 `POST /attachments`（objectType/objectID）通道重试
- 若 `/attachments` 也失败，临时方案：脚本在 steps 中保留附件路径 + `_attachments` 注明失败文件，通过 Web 界面手动关联

### 4. 获取版本列表返回 "Need project id."
- 该禅道实例需要通过 `--project-id` 参数查询版本
- 从产品详情中获取对应的 project id

### 5. 获取用户列表返回 "no company-browse priv."
- 当前账号没有公司浏览权限，忽略即可
- 指派时可不传 `assigned-to`，或手动指定已知账号

### 6. SSL 证书错误
- 内网部署常使用自签名证书，调用时关闭 SSL 校验（`--no-verify` 或 `verify_ssl=False`）

### 7. Token 过期
- Token 通常有有效期（默认 24 小时，具体看后台配置）
- 脚本中每次操作前自动重新登录，无需手动处理
