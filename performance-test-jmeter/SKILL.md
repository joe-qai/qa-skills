---
name: performance-test-jmeter
description: Use this skill when you need to generate executable JMeter test plans (.jmx) from API specs or business scenarios; triggers include JMeter performance testing, 性能测试脚本, 生成jmeter脚本, jmeter脚本, and performance-test-jmeter.
---

# JMeter 性能测试

## 何时使用

- 用户提供 API 接口文档或业务场景，需要生成**可直接执行的 JMeter 脚本**（.jmx）。
- 需要对已有 JMeter 脚本做优化、扩展或问题排查。

## 输入要求

用户提供以下信息（缺什么问什么，不要猜）：

| 必填 | 字段 | 说明 |
|------|------|------|
| ✅ | 目标接口/场景 | 接口路径、方法、参数，或业务场景描述 |
| ✅ | 并发模型 | 并发用户数、Ramp-Up 时间、持续时长 |
| ⬜ | 性能阈值 | 响应时间 P95/P99、错误率上限、吞吐量目标 |
| ⬜ | 测试数据 | CSV 数据源、登录凭证、业务参数 |
| ⬜ | 环境信息 | 测试环境 URL、网络条件、证书配置 |

## 执行流程

### 1. 输入审计

- 检查接口信息是否完整（路径、方法、参数、鉴权）
- 检查并发模型是否合理（线程数、Ramp-Up、循环次数）
- 缺失信息标记为「假设」并给出默认值

### 2. 脚本生成

基于输入生成完整 .jmx 文件，包含：

```
TestPlan
├── ThreadGroup（线程数、Ramp-Up、循环）
├── HTTPSampler（路径、方法、Header、Body）
├── CSVDataSet（数据源配置）
├── ResponseAssertion（状态码、JSON Path、文本匹配）
├── DurationAssertion（响应时间上限）
├── UnifiedRequestResults（结果监听器）
└── SummaryReport（汇总报告）
```

### 3. 脚本校验

生成后必须执行以下校验：

- [ ] .jmx 是合法 XML（无未闭合标签、无非法字符）
- [ ] ThreadGroup 参数完整（线程数、Ramp-Up、循环均 > 0）
- [ ] 每个 HTTPSampler 有正确的 Method 和 Path
- [ ] CSV DataSet 若存在，文件路径有效且变量名被引用
- [ ] Assertion 存在且条件明确（非空字符串）
- [ ] 无硬编码的生产环境 URL
- [ ] 密钥/Token 使用占位符 `${__ENV(VAR_NAME)}` 而非明文

### 4. 输出交付物

| 文件 | 内容 |
|------|------|
| `test-plan.jmx` | 完整可执行的 JMeter 测试脚本 |
| `run-test.sh` | 一键执行命令（非 GUI 模式 + HTML 报告） |
| `README.md` | 脚本说明：场景、参数、执行方式、注意事项 |

**执行命令**（自动写入 run-test.sh）：
```bash
jmeter -n -t test-plan.jmx -l results.jtl -e -o ./html-report
```

### 5. 自检清单

- [ ] 覆盖所有用户提供的接口/场景
- [ ] 并发模型与用户预期一致
- [ ] 阈值断言已设置
- [ ] 测试数据可获取（非硬编码）
- [ ] 脚本可在目标环境直接运行

## 核心约束

- 输出必须是**可执行的 .jmx 文件**，不是文档或方案。
- 按风险/业务影响排优先级，不要平均铺满。
- 密钥、Token 只用环境变量占位符，禁止真实值。
- 信息不完整时先给可用版本，标清假设，不要停在提问。

## 参考文件

- `prompts/performance-test-jmeter.md`：详细执行规范（覆盖清单、输出结构、质量要求）。
- `references/framework-spec.md`：JMeter 工具专项结构。
- `references/setup-and-ci.md`：安装、CI 集成说明。

## 常见误区

- 只给方案文档不给脚本 → 必须输出 .jmx。
- 所有接口同等并发 → 应按业务权重分配。
- 跳过假设说明 → 无 SLA 时所有数字标「假设」。
- 硬编码密钥 → 用 `${__ENV(...)}` 占位。
