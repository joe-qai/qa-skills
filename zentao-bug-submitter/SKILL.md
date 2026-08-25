---
name: zentao-bug-submitter
description: "自动在禅道（ZenTao）系统提交 Bug。当用户提供测试用例描述、重现步骤、预期结果、实际结果、截图/视频/日志等附件，并要求提交 Bug、提缺陷、报 bug、创建 bug、提交到禅道时使用。支持动态选择所属产品、模块、影响版本、指派人，自动上传附件并关联。基于禅道 REST API v1，兼容企业版/旗舰版/开源版。"
---

# 禅道 Bug 自动提交

通过禅道 REST API v1 自动提交 Bug，支持账号密码登录、动态获取产品/模块/版本/用户选项。
**注意**：附件上传接口（`POST /api.php/v1/files`）在某些禅道实例中存在服务端问题，如遇到上传失败请记录 uid 并通过禅道 Web 界面手动关联。

## 预设连接信息

- **禅道地址**: `https://pm.dding.net/zentao`
- **账号**: `xuping`
- **密码**: 由用户提供或通过环境变量 `ZENTAO_PASSWORD` 传入
- **SSL**: 内网可能为自签名证书，如遇证书错误加 `--no-verify`

> 脚本路径: `scripts/zentao_client.py`
> 详细 API 字段和枚举值: 见 [references/api_reference.md](references/api_reference.md)

## 工作流

收到提交 Bug 的请求后，按以下步骤执行：

### Step 1: 提取 Bug 信息

从用户输入中提取以下内容：

| 信息 | 来源 | 必填 |
|------|------|------|
| Bug 标题 | 用户描述/用例标题 | 是 |
| 重现步骤 | 用例步骤/操作描述 | 是 |
| 预期结果 | 用例预期 | 是 |
| 实际结果 | 用户描述的异常现象 | 是 |
| 所属产品 | 用户指定，**未指定时必须询问确认** | 是 |
| 严重程度 | 用户指定，或根据影响判断（默认3） | 是 |
| 优先级 | 用户指定，或根据严重程度推断（默认3） | 是 |
| 附件 | 用户上传的截图/视频/日志文件 | 否 |
| 操作系统/浏览器 | 用户描述的环境 | 否 |

如果用户未明确指定严重程度和优先级，按以下规则推断：
- 系统崩溃/数据丢失/核心功能不可用 → severity=1, pri=1（P1）
- 主要功能异常 → severity=3, pri=3（P2）
- 功能异常但有替代方案 → severity=3, pri=3（P2）
- 界面/文案问题 → severity=4, pri=4（P3）
- 优化建议 → severity=5, pri=5（P4）
> **注意**：部分禅道实例的严重度/优先级标签与数值映射为 1→P1、3→P2、4→P3，跳过 2。创建前请确认产品的实际映射配置。

### Step 2: 获取动态选项

**所属产品为必填字段**。若用户未明确指定产品，必须先向用户询问并确认产品后再继续。

所属模块、影响版本、当前指派这四个字段需要动态获取。按顺序调用：

```bash
# 2a. 获取产品列表（让用户选择，或根据关键词匹配）
python scripts/zentao_client.py products --url https://pm.dding.net/zentao --account xuping --password '<密码>'

# 2b. 根据选定产品获取模块列表
python scripts/zentao_client.py modules --product-id <产品ID> --url ... --account ... --password ...

# 2c. 获取版本列表（注意：此禅道实例需要通过 project-id 查询）
# 先从产品详情中获取 project id（如 X-Men 产品对应 project=182）
python scripts/zentao_client.py builds --project-id <项目ID> --url ... --account ... --password ...

# 若 builds 查询返回 403（账号无项目浏览权限），可直接让用户提供版本号字符串（如 "601_28"、"APP_601_28"）

# 2d. 获取用户列表（部分实例可能无权限，忽略即可）
python scripts/zentao_client.py users --url ... --account ... --password ...
```

**选择策略：**
- 如果用户明确指定了产品/模块/版本/指派人名称，从返回列表中模糊匹配对应 ID
- 如果用户未指定，向用户展示选项列表让其选择（产品和版本通常必须选）
- 模块如果用户不关心，可传 `0` 或不传
- 指派人如果用户未指定，可不传（默认留空）
- **版本名模糊匹配**：若用户输入的版本号（如 `601_28`）与已有版本不完全一致，脚本会自动从产品已有 Bug 中提取所有 openedBuild 进行模糊匹配，找到最接近的已有版本名（如 `APP_601_28`）
- **执行项自动注入**：创建 Bug 时若未指定 `--execution`，脚本会自动查询产品的执行列表并注入，确保版本名正确解析

### Step 3: 构造重现步骤 (steps)

**使用 plain text 格式**（非 HTML），各板块之间用 `\n\n` 分隔，板块名称用中文方括号标注：

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

### Step 4: 上传附件（如有）

如果用户提供了截图、视频、日志等文件，尝试上传。脚本按 **REST /files → REST /attachments（objectType/objectID）** 两级策略自动上传并关联。

```bash
# 方式一：create-bug 时直接带附件（先 POST /files 上传，再通过 uid 关联到 Bug）
python scripts/zentao_client.py create-bug \
  --product-id <产品ID> --title "Bug 标题" --severity 3 --pri 3 \
  --opened-build <版本ID> --steps "..." \
  --files /path/to/screenshot.png /path/to/run.log \
  --url https://pm.dding.net/zentao --account xuping --password '<密码>'

# 方式二：仅上传附件（纯 REST /files）
python scripts/zentao_client.py upload \
  --file /path/to/screenshot.png --uid bug-upload-<timestamp> \
  --url https://pm.dding.net/zentao --account xuping --password '<密码>'

# 方式三：批量上传（多附件，同一 uid 关联）
python scripts/zentao_client.py upload-files \
  --files /path/a.png /path/run.log --uid bug-upload-<timestamp> \
  --url https://pm.dding.net/zentao --account xuping --password '<密码>'
```

多个文件使用**同一个 uid** 依次上传。

**上传策略（`add_or_upload_attachments`）：**
1. 优先 REST `POST /files`（multipart，field 名 `file`），成功后附件通过 uid 自动关联到 Bug。
2. 若 `/files` 失败，对失败文件回退到 `POST /attachments`（objectType=bug，objectID=<已创建 Bug 的 id>）上传并直接关联。
3. 两条 REST 通道均失败时，**不阻断建单**：在创建 Bug 时把附件路径写进 steps，返回结果中带 `_attachments` 字段逐文件标注 `ok/channel/message`，需通过禅道 Web 界面手动关联。

> **注意**：部分禅道实例的 `/api.php/v1/files` 接口存在服务端问题（返回 `{"error":"error"}`），
> 此时脚本会回退到 `/attachments` 通道；若 `/attachments` 也失败，请按 `_attachments` 的结果把失败文件的路径告知用户，并在 steps 中保留附件路径。

### Step 5: 创建 Bug

```bash
python scripts/zentao_client.py create-bug \
  --product-id <产品ID> \
  --title "Bug 标题" \
  --severity <1-5> \
  --pri <1-5> \
  --opened-build <版本ID> \
  --steps "【前置条件】\n  xxx\n\n【测试步骤】\n  1. xxx" \
  --module <模块ID> \
  --assigned-to <用户账号> \
  --uid <附件关联uid> \
  --os "操作系统" \
  --browser "浏览器" \
  --url https://pm.dding.net/zentao --account xuping --password '<密码>'
```

### Step 6: 返回结果

创建成功后，向用户报告：
- Bug 编号（返回的 `id`）
- Bug 标题
- Bug 链接: `https://pm.dding.net/zentao/bug-view-<id>.html`
- 附件关联情况：若 `_attachments` 中有 `ok=false` 的文件，说明该实例服务端限制自动上传，需通过 Web 界面手动关联，并附上本地文件路径

## 作为 Python 模块使用

复杂场景（如批量提交、循环处理）可直接 import：

```python
import sys
sys.path.insert(0, '/path/to/zentao-bug-submitter/scripts')
from zentao_client import ZentaoClient

client = ZentaoClient(
    base_url='https://pm.dding.net/zentao',
    account='xuping',
    password='<密码>',
    verify_ssl=False,  # 内网自签名证书
)

# 自动登录
client.ensure_login()

# 获取选项
products = client.get_products()
modules = client.get_modules(product_id=1)

# 创建 Bug（steps 使用 plain text 格式）
bug = client.create_bug(
    product_id=1,
    module=5,
    title='登录页面崩溃',
    severity=2,
    pri=2,
    opened_build=3,
    assigned_to='zhangsan',
    steps='【前置条件】\n  用户已登录系统\n\n【测试步骤】\n  1. 打开登录页面\n  2. 输入错误密码\n  3. 点击登录\n\n【实际结果】\n  页面崩溃\n\n【预期结果】\n  提示密码错误',
    os='Windows 11',
    browser='Chrome 120',
)
print(f"Bug #{bug['id']} 创建成功")
```

## 字段速查

| 禅道字段 | 脚本参数 | 说明 |
|----------|----------|------|
| 所属产品 | `--product-id` | 产品 ID，从 products 获取 |
| 所属模块 | `--module` | 模块 ID，从 modules 获取，可选 |
| 影响版本 | `--opened-build` | 版本 ID 或名称，从 builds 获取；支持字符串（如 `APP_601_28`、`601_28`），可多个。若输入模糊（如 `601_28`），脚本自动模糊匹配到已有版本名 |
| 当前指派 | `--assigned-to` | 用户 account（不是姓名），从 users 获取；部分实例无权限时直接传已知账号 |
| Bug 标题 | `--title` | 简短描述问题 |
| 严重程度 | `--severity` | 1-5，1最严重 |
| 优先级 | `--pri` | 1-5，1最高 |
| Bug 类型 | `--bug-type` | 默认 codeerror，详见参考文档 |
| 重现步骤 | `--steps` | plain text 格式，见上方步骤3 |
| 附件 | `--files` / `--uid` | 文件路径或已上传的 uid |
| 操作系统 | `--os` | 如 "Windows 11" |
| 浏览器 | `--browser` | 如 "Chrome 120" |

完整字段说明、枚举值和常见问题: [references/api_reference.md](references/api_reference.md)

## 注意事项

1. **密码安全**: 不要在回复中明文展示密码。通过环境变量 `ZENTAO_PASSWORD` 或命令行参数传入，执行时不在输出中回显。
2. **SSL 证书**: 内网地址如报 SSL 错误，加 `--no-verify` 参数。
3. **必填字段**: 不同禅道后台配置可能有不同的必填字段。如果创建失败，仔细阅读错误信息补充缺失字段。**openedBuild 不可为 0，必须传有效版本 ID**。
4. **附件上传**: 部分禅道实例的附件上传接口存在服务端问题（返回 `{"error":"error"}`），此时可跳过附件步骤。
5. **Token 过期**: 脚本每次操作前自动检查登录状态，token 过期会自动重新登录。
6. **版本查询**: builds 接口在某些禅道实例中需要通过 `--project-id` 而非 `--product-id` 查询。
