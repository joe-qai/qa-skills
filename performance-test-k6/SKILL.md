---
name: performance-test-k6
description: Use this skill when you need to generate executable k6 load/stress/spike/soak test scripts from API specs or business scenarios; triggers include k6, k6 性能测试, 生成k6脚本, k6脚本, and k6 performance testing.
---

# k6 性能测试

## 何时使用

- 用户提供 API 接口或业务场景，需要生成**可直接执行的 k6 测试脚本**（.js）。
- 需要对已有 k6 脚本做优化、扩展或结果分析。

## 输入要求

| 必填 | 字段 | 说明 |
|------|------|------|
| ✅ | 目标接口/场景 | 接口路径、方法、参数，或业务场景描述 |
| ✅ | 测试类型 | load / stress / spike / soak / smoke（选一或多选） |
| ⬜ | 并发模型 | VU 数、RPS 目标、持续时长、阶段配置 |
| ⬜ | 性能阈值 | 响应时间 P95/P99、错误率上限 |
| ⬜ | 测试数据 | 请求体、参数化数据、登录凭证 |
| ⬜ | 环境信息 | BASE_URL、环境名、网络条件 |

## 执行流程

### 1. 输入审计

- 检查接口信息是否完整（路径、方法、参数、鉴权）
- 检查测试类型是否匹配业务目标
- 缺失信息标记为「假设」并给出默认值

### 2. 脚本生成

基于输入，复用 `scripts/` 框架生成测试文件：

```
scripts/
├── config.js          # 已有：baseURL、阈值、示例数据（按需修改）
├── helpers.js         # 已有：get/post/assertOk/think 工具函数
├── tests/
│   ├── load.js        # 已有模板：按需生成新场景文件
│   ├── stress.js
│   ├── spike.js
│   ├── soak.js
│   └── api-smoke.js
└── tools/
    ├── summarize_k6.py    # 已有：汇总报告
    ├── compare_k6.py      # 已有：对比历史结果
    └── local_mock_server.py  # 已有：本地 mock
```

**生成规则**：
- 新测试文件放在 `tests/` 目录，命名 `<场景>.js`
- 复用 `helpers.js` 的 `get/post/assertOk/think` 函数
- 复用 `config.js` 的 `common/thresholds/tags`
- 若用户场景与已有模板（load/stress/spike/soak/smoke）匹配，基于模板修改而非从零写

### 3. 脚本校验

生成后必须执行以下校验：

- [ ] JS 语法正确（无未闭合括号、无 import 路径错误）
- [ ] `options` 对象包含 `scenarios` 和 `thresholds`
- [ ] 使用 `helpers.js` 的函数而非直接调用 `http.*`
- [ ] 环境变量通过 `__ENV` 读取，无硬编码密钥
- [ ] `tags()` 函数调用包含 testType 和 module 参数
- [ ] threshold 阈值与用户要求一致（或标明默认值）

### 4. 输出交付物

| 文件 | 内容 |
|------|------|
| `tests/<场景>.js` | 可执行的 k6 测试脚本 |
| `run-test.sh` | 一键执行命令 |
| `README.md` | 脚本说明：场景、参数、执行方式 |

**执行命令**（自动写入 run-test.sh）：
```bash
# 基础执行
k6 run tests/<场景>.js

# 指定环境
BASE_URL=https://api.example.com ENV=staging k6 run tests/<场景>.js

# 导出汇总 JSON
K6_SUMMARY_EXPORT=summary.json k6 run tests/<场景>.js
```

### 5. 自检清单

- [ ] 覆盖用户指定的测试类型（load/stress/spike/soak/smoke）
- [ ] 每个接口有独立的 check 断言
- [ ] 阈值设置合理（有默认值或用户指定）
- [ ] 测试数据可获取（非硬编码）
- [ ] 脚本可直接 `k6 run` 执行

## 核心约束

- 输出必须是**可执行的 .js 脚本**，不是文档或方案。
- 复用已有框架（config.js / helpers.js），不重写基础函数。
- 默认只选最关键的 1～2 类场景，不要全做。
- 密钥、Token 只用 `__ENV` 占位，禁止真实值。

## 参考文件

- `prompts/performance-test-k6.md`：详细执行规范。
- `references/framework-spec.md`：k6 框架结构说明。
- `scripts/`：完整可复用的脚本框架。

## 常见误区

- 只给方案不给脚本 → 必须输出可执行 .js。
- 每次从零写全部脚本 → 复用已有模板和工具函数。
- 默认全做基线/负载/压力/尖峰/稳定性 → 按优先级选 1～2 类。
- 硬编码密钥 → 用 `__ENV` 占位。
