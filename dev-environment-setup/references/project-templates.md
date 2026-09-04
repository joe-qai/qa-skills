# 项目模板目录结构

## Django 项目

```
project-name/
├── config/                    # Django 配置
│   ├── __init__.py
│   ├── settings.py            # 主配置
│   ├── urls.py                # URL 路由
│   ├── wsgi.py
│   └── asgi.py
├── apps/                      # 应用目录
│   ├── __init__.py
│   └── users/                 # 用户应用示例
│       ├── __init__.py
│       ├── migrations/
│       ├── admin.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
├── static/                    # 静态文件
├── media/                     # 上传文件
├── tests/                     # 测试目录
│   ├── __init__.py
│   ├── conftest.py
│   └── test_users.py
├── .env.example               # 环境变量模板
├── .gitignore
├── manage.py
├── requirements.txt           # 生产依赖
├── requirements-dev.txt       # 开发依赖
└── docker-compose.yml         # 可选
```

## FastAPI 项目

```
project-name/
├── app/
│   ├── __init__.py
│   ├── main.py                # 应用入口
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # 配置
│   │   └── dependencies.py    # 依赖注入
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py        # 认证路由
│   │       └── items.py       # 业务路由
│   ├── models/
│   │   └── base.py            # 基础模型
│   ├── schemas/
│   │   └── item.py            # Pydantic schema
│   ├── services/              # 业务逻辑层
│   └── utils/                 # 工具函数
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── api/
├── pyproject.toml
├── requirements.txt
├── .env.example
└── pytest.ini
```

## Vue 3 + TypeScript 项目

```
project-name/
├── public/
├── src/
│   ├── main.ts                # 入口文件
│   ├── App.vue                # 根组件
│   ├── router/
│   │   └── index.ts           # 路由配置
│   ├── stores/
│   │   └── counter.ts         # Pinia 状态管理
│   ├── views/
│   │   └── HomeView.vue
│   ├── components/
│   │   └── HelloWorld.vue
│   ├── types/                 # TypeScript 类型定义
│   ├── utils/                 # 工具函数
│   └── assets/                # 静态资源
├── test/
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── package.json
└── .env.example
```

## Go (Gin/Fiber) 项目

```
project-name/
├── cmd/
│   └── server/
│       └── main.go            # 程序入口
├── internal/
│   ├── server/                # HTTP 服务器
│   │   └── server.go
│   ├── handler/               # HTTP 处理器
│   │   └── handler.go
│   ├── middleware/            # 中间件
│   │   └── middleware.go
│   ├── config/                # 配置管理
│   │   └── config.go
│   ├── repository/            # 数据访问层
│   │   └── repository.go
│   ├── model/                 # 数据模型
│   └── service/               # 业务逻辑层
├── pkg/                       # 公共包
├── test/
├── docs/                      # 文档
├── go.mod
├── go.sum
├── Makefile
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## Spring Boot 项目

```
project-name/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/demo/
│   │   │       ├── DemoApplication.java  # 启动类
│   │   │       ├── controller/           # 控制器层
│   │   │       │   └── HealthController.java
│   │   │       ├── service/              # 服务层
│   │   │       │   └── impl/
│   │   │       ├── repository/           # 数据访问层
│   │   │       ├── model/                # 实体类
│   │   │       │   └── BaseEntity.java
│   │   │       ├── dto/                  # 数据传输对象
│   │   │       └── config/               # 配置类
│   │   │           └── SecurityConfig.java
│   │   └── resources/
│   │       └── application.yml
│   └── test/
│       └── java/
│           └── com/example/demo/
│               └── DemoApplicationTests.java
├── docs/
├── pom.xml
└── .gitignore
```
