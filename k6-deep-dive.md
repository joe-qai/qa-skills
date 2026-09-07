# k6 深度学习指南

> 基于 `naodeng/awesome-qa-skills` 的 performance-test-k6 skill + 官方文档整理
> 生成时间：2026-09-05

---

## 一、k6 是什么？

k6 是一款**开源的负载测试工具**，由 Grafana Labs 开发。它的核心理念是：**用 JavaScript 写压测脚本，像写代码一样做性能测试**。

| 维度 | k6 | JMeter | Locust |
|------|-----|--------|--------|
| 脚本语言 | JavaScript (ES6) | Java XML / Groovy | Python |
| 执行引擎 | Go（单进程多线程） | Java JVM | Python 多线程 |
| 架构 | 轻量 CLI 工具 | GUI + 命令行 | 分布式 Web |
| 资源占用 | 极低（Go 编译产物） | 高（JVM + GUI） | 中（Python GIL 限制） |
| CI/CD 集成 | 一行命令，内置 JSON 报告 | 需配置插件或 JMX 导出 | 需 Docker 或 CI 配置 |
| 可视化 | 内置 summary + Grafana 集成 | 内置 HTML 报告 | Web UI |

---

## 二、为什么 k6 近年流行？

### 2.1 对比 JMeter

```
JMeter 的痛点：
├─ GUI 太重，无法 CI/CD 化
├─ XML 配置难以版本管理
├─ 脚本非代码化，复用困难
├─ JVM 内存占用大，多并发压力大
└─ 报告样式老旧，难以定制

k6 的解法：
├─ 纯 CLI，一行命令启动
├─ 脚本即代码（JS），Git 友好
├─ Go 编写，单机可模拟数万 VU
├─ 内置 JSON 输出，Grafana/InfluxDB 直连
└─ 响应式阈值，不达标自动退出
```

### 2.2 对比 Locust

```
Locust 的痛点：
├─ Python GIL 限制单机并发上限（~几百 VU）
├─ 分布式需要额外部署 Master/Worker
├─ 大规模压测时内存增长明显
└─ 脚本写 Python，不适合前端测试团队

k6 的解法：
├─ Go 无 GIL，单机轻松 10k+ VU
├─ 内置虚拟用户模型，无需集群即可水平扩展
├─ 内存占用恒定，不随 VU 数线性增长
└─ JS 脚本，前端/后端工程师都能写
```

---

## 三、核心概念速查

### 3.1 虚拟用户（VU）

k6 的最小执行单元是 Virtual User。每个 VU 是一个独立的 JavaScript 执行环境，模拟一个真实用户。

```js
export const options = {
  scenarios: {
    contacts: {
      executor: 'shared-iterations',  // 所有 VU 共享迭代次数
      vus: 5,                          // 最多 5 个并发 VU
      iterations: 10,                  // 总共执行 10 次
    },
  },
};
```

### 3.2 执行器（Executor）

| Executor | 用途 | 典型场景 |
|----------|------|---------|
| `ramping-vus` | 逐步升降并发 | 负载测试 |
| `constant-vus` | 固定并发 | 稳定性测试 |
| `constant-arrival-rate` | 固定 RPS | 精确流量控制 |
| `shared-iterations` | 共享迭代 | 快速冒烟 |
| `per-vu-iterations` | 每 VU 独立迭代 | 单次流程复现 |
| `externally-controlled` | 外部控制 | 与 orchestrator 配合 |

### 3.3 阈值（Thresholds）

阈值是 k6 的核心：不达标自动 fail，适合 CI/CD 门禁。

```js
thresholds: {
  http_req_failed:       ['rate<0.01'],      // 失败率 < 1%
  http_req_duration:     ['p(95)<500'],      // p95 < 500ms
  http_req_duration:     ['avg<200', 'p(99)<1000'], // 多条件
  iteration_duration:    ['avg<3000', 'p(90)<5000'],
  checks:                ['rate>0.95'],       // 检查通过率 > 95%
}
```

### 3.4 场景（Scenarios）

一个脚本可以有多个场景，用 `tags` 区分接口，用 `groups` 分类逻辑。

```js
export const options = {
  scenarios: {
    homepage: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 50 },   // 1分钟内升到50 VU
        { duration: '5m', target: 50 },   // 稳态5分钟
        { duration: '1m', target: 0 },    // 1分钟降为0
      ],
      tags: { module: 'homepage' },
    },
    api_search: {
      executor: 'constant-arrival-rate',
      rate: 20,                           // 每秒20次请求
      timeUnit: '1s',
      preAllocatedVUs: 10,
      maxVUs: 50,
      tags: { module: 'api' },
    },
  },
  thresholds: {
    'http_req_duration{module:homepage}': ['p(95)<500'],
    'http_req_duration{module:api}': ['p(95)<200'],
  },
};
```

---

## 四、脚本结构模板

### 4.1 项目结构

```
perf/
├── scripts/
│   ├── config.js          # 公共配置（baseURL、默认headers、阈值）
│   ├── helpers.js         # 封装 GET/POST/断言/ThinkTime
│   ├── tests/
│   │   ├── api-smoke.js   # 冒烟测试
│   │   ├── load.js        # 负载测试
│   │   ├── spike.js       # 尖峰测试
│   │   ├── stress.js      # 压力测试
│   │   └── soak.js        # 稳定性测试
│   └── run-tests.sh       # 执行入口
├── data/                   # CSV/JSON 测试数据
├── .env                    # 环境变量（BASE_URL 等）
└── README.md
```

### 4.2 config.js（公共配置）

```js
import { SharedArray } from 'k6/data';

const target = __ENV.BASE_URL || 'https://test.k6.io';
const envName = __ENV.ENV || 'staging';

export const common = {
  baseURL: target,
  env: envName,
  defaultHeaders: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${__ENV.API_TOKEN || ''}`,
  },
};

// 全局阈值（可在各场景覆盖）
export const thresholds = {
  http_req_failed: ['rate<0.01'],
  http_req_duration: ['p(95)<800', 'p(99)<1500'],
};

// 共享测试数据
export const samplePayloads = new SharedArray('sample-payloads', () => [
  { skuId: 'SKU-1001', userTier: 'PLUS' },
  { skuId: 'SKU-1002', userTier: 'NORMAL' },
]);

// 标签工厂
export function tags(testType, module) {
  return { test_type: testType, module, env: common.env };
}
```

### 4.3 helpers.js（请求封装）

```js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { common } from './config.js';

export function get(path, tags = {}) {
  return http.get(`${common.baseURL}${path}`, {
    headers: common.defaultHeaders,
    tags,
  });
}

export function post(path, body, tags = {}) {
  return http.post(`${common.baseURL}${path}`, JSON.stringify(body), {
    headers: { ...common.defaultHeaders, 'Content-Type': 'application/json' },
    tags,
  });
}

export function assertOk(res, extraChecks = {}) {
  check(res, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
    ...extraChecks,
  });
}

export function think(minSec = 0.5, maxSec = 1.5) {
  sleep(minSec + Math.random() * Math.max(maxSec - minSec, 0));
}
```

### 4.4 load.js（负载测试脚本）

```js
import { assertOk, get, think } from '../helpers.js';
import { tags, thresholds } from '../config.js';

export const options = {
  scenarios: {
    load_test: {
      executor: 'ramping-vus',
      startVUs: 5,
      stages: [
        { duration: '2m', target: 30 },   // 热身
        { duration: '5m', target: 80 },    // 稳态
        { duration: '2m', target: 0 },     // 冷却
      ],
      gracefulRampDown: '30s',
      tags: tags('load', 'homepage'),
    },
  },
  thresholds,
};

export default function () {
  const res = get('/');
  assertOk(res, {
    'body has html': (r) => String(r.body || '').includes('<html'),
  });
  think();
}
```

### 4.5 spike.js（尖峰测试）

```js
import { assertOk, get, post } from '../helpers.js';
import { tags, thresholds } from '../config.js';

export const options = {
  scenarios: {
    spike_test: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '30s', target: 10 },   // 基线
        { duration: '10s', target: 200 },   // 尖峰：瞬时冲高
        { duration: '30s', target: 10 },    // 回落
        { duration: '2m', target: 10 },     // 观察恢复
      ],
      gracefulRampDown: '10s',
      tags: tags('spike', 'homepage'),
    },
  },
  thresholds: {
    ...thresholds,
    'http_req_duration{scenario:spike_test}': ['p(95)<2000'],
  },
};

export default function () {
  const res = get('/');
  assertOk(res);
  think(0.1, 0.5);
}
```

---

## 五、执行与报告

### 5.1 本地执行

```bash
# 基本执行
k6 run scripts/tests/load.js

# 指定环境变量
export BASE_URL=https://staging.example.com
k6 run --env ENV=staging scripts/tests/load.js

# 输出 JSON 报告（适合 CI/CD）
k6 run --out json=report.json scripts/tests/load.js

# 内置 summary 模式
k6 run --summary-export=summary.json scripts/tests/load.js
```

### 5.2 报告查看

```bash
# 命令行 summary（默认）
k6 run scripts/tests/load.js

# 用 Python 工具解析
python scripts/tools/summarize_k6.py report.json
# 输出: { "p95_ms": 234, "p99_ms": 512, "error_rate": 0.002, "rps": 85.3 }
```

### 5.3 Grafana 集成（推荐生产方案）

```bash
# k6 直接输出到 InfluxDB
k6 run --out influx=http://localhost:8086/k6 scripts/tests/load.js

# 或用 k6 cloud（商业化托管）
k6 cloud scripts/tests/load.js
```

---

## 六、关键 API 速查

### 6.1 http 模块

```js
import http from 'k6/http';

// GET
const res = http.get('https://test.k6.io/', { tags: { name: 'get' } });

// POST with JSON body
const res = http.post('https://test.k6.io/api/items', JSON.stringify({ name: 'item' }), {
  headers: { 'Content-Type': 'application/json' },
  tags: { name: 'post' },
});

// 带参数
const res = http.get('https://test.k6.io/items?id=1&limit=10');

// 响应属性
res.status        // HTTP 状态码
res.body          // 响应体（字符串）
res.json()        // 解析为 JSON 对象
res.headers       // 响应头
res.timings       // 耗时详情
res.checks        // 通过的检查数
```

### 6.2 check 断言

```js
import { check } from 'k6';

check(res, {
  'status is 200': (r) => r.status === 200,
  'response has user_id': (r) => {
    const body = r.json();
    return body.hasOwnProperty('user_id');
  },
  'response time < 500ms': (r) => r.timings.duration < 500,
});
```

### 6.3 group 分组

```js
import { group } from 'k6';

export default function () {
  group('登录流程', function () {
    const loginRes = http.post('/api/login', JSON.stringify({ user: 'test', pass: '123' }));
    check(loginRes, { 'login ok': (r) => r.status === 200 });
  });

  group('浏览商品', function () {
    const itemsRes = http.get('/api/items');
    check(itemsRes, { 'items loaded': (r) => r.json().length > 0 });
  });
}
```

### 6.4 data 共享数据

```js
import { SharedArray } from 'k6/data';
import { randomIntBetween } from 'k6/math';

// 一次性加载到内存，所有 VU 共享只读
const users = new SharedArray('users', () =>
  Array.from({ length: 1000 }, (_, i) => ({ id: i + 1, name: `user${i + 1}` }))
);

export default function () {
  const user = users[randomIntBetween(0, users.length - 1)];
  // 使用 user...
}
```

### 6.5 params 参数化

```js
import { ParametricArray } from 'k6/data';

const payloads = new ParametricArray('payloads', () => [
  { qty: 1 }, { qty: 5 }, { qty: 10 }, { qty: 100 },
]);

export default function () {
  const payload = payloads.next();
  http.post('/api/order', JSON.stringify(payload));
}
```

---

## 七、五种性能测试场景

| 场景 | 目的 | executor 推荐 | 典型配置 |
|------|------|--------------|---------|
| **Baseline** | 首次摸底，建立性能基准 | `ramping-vus` | 低 VU，短时长 |
| **Load** | 验证目标并发下是否达标 | `ramping-vus` | 逐步升到目标 VU，稳态运行 |
| **Stress** | 找容量上限，观察降级点 | `ramping-vus` | 持续加压直到失败 |
| **Spike** | 验证瞬时流量冲击后的恢复能力 | `ramping-vus` | 快速冲高再回落 |
| **Soak** | 长稳测试，检测内存泄漏 | `constant-vus` | 低 VU，运行数小时 |

---

## 八、与 JMeter / Locust 选型决策

```
需要快速出脚本、CI/CD 集成 → k6
需要 GUI 操作、非技术成员参与 → JMeter
已有 Python 团队、脚本简单 → Locust
大规模分布式压测（10万+ VU）→ k6 cloud / k6 集群
需要录制回放 → JMeter
需要复杂协议（LDAP、SOAP）→ JMeter
前端测试团队主导 → k6（JS 友好）
```

---

## 九、安装 k6

### Windows

```powershell
# Scoop
scoop install k6

# Chocolatey
choco install k6

# 或者直接从 GitHub Release 下载
# https://github.com/grafana/k6/releases
```

### macOS / Linux

```bash
# Homebrew
brew install k6

# 或者
curl -sSfL https://github.com/grafana/k6/releases/download/v0.52.0/k6-v0.52.0-windows-amd64.zip \
  -o k6.zip && unzip k6.zip && mv k6-windows-amd64/k6.exe /usr/local/bin/
```

### 验证安装

```bash
k6 version
# k6 v0.52.0 ((unknown), commit ..., built at ...
```

---

## 十、参考资源

- 官方文档：https://k6.io/docs/
- 在线 playground：https://play.k6.io
- awesome-qa-skills k6 skill：`skills/zh/testing-types/performance-test-k6/`
- k6 GitHub：https://github.com/grafana/k6
- k6 示例仓库：https://github.com/grafana/k6/tree/master/examples
