#!/usr/bin/env python3
"""
FastAPI Project Scaffold Generator
Creates a new FastAPI project with recommended structure and tooling.
"""

import argparse
import sys
from pathlib import Path


def generate_structure(project_dir: Path):
    """Generate FastAPI project directory structure and files."""
    structure = {
        ".env.example": '''DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
DEBUG=True
''',
        ".gitignore": '''__pycache__/
*.pyc
*.pyo
env/
venv/
.venv/
*.sqlite3
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage
.DS_Store
''',
        "pyproject.toml": '''[project]
name = "fastapi-app"
version = "0.1.0"
description = "A FastAPI project"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlalchemy>=2.0.0",
    "asyncpg>=0.30.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.9",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "apscheduler>=3.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0",
    "httpx>=0.27.0",
    "ruff>=0.8.0",
    "mypy>=1.0",
    "pre-commit>=4.0",
]

[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
''',
        "requirements.txt": '''fastapi>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy>=2.0.0
asyncpg>=0.30.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
pydantic>=2.0.0
pydantic-settings>=2.0.0
''',
        "requirements-dev.txt": '''-r requirements.txt
pytest>=8.0
pytest-asyncio>=0.24.0
pytest-cov>=6.0
httpx>=0.27.0
ruff>=0.8.0
mypy>=1.0
pre-commit>=4.0
''',
    }

    # Create directories
    dirs = [
        "app",
        "app/api",
        "app/api/v1",
        "app/core",
        "app/models",
        "app/schemas",
        "app/services",
        "app/utils",
        "tests",
        "tests/api",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
        init_file = project_dir / d / "__init__.py"
        if d.startswith("app"):
            init_file.touch()

    # Main app file
    (project_dir / "app" / "__init__.py").write_text('')
    (project_dir / "app" / "main.py").write_text('''"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.v1 import auth, items  # noqa: E402
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(items.router, prefix="/api/v1/items", tags=["items"])

    return app


app = create_app()
''')

    # Config
    (project_dir / "app" / "core" / "__init__.py").write_text('')
    (project_dir / "app" / "core" / "config.py").write_text('''"""Application settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI App"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production"
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/db"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
''')

    (project_dir / "app" / "core" / "dependencies.py").write_text('''"""Shared dependencies."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    # TODO: Implement JWT validation
    return {"sub": "current_user"}
''')

    # Models
    (project_dir / "app" / "models" / "__init__.py").write_text('')
    (project_dir / "app" / "models" / "base.py").write_text('''"""Base SQLAlchemy model."""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
''')

    # Schemas
    (project_dir / "app" / "schemas" / "__init__.py").write_text('')
    (project_dir / "app" / "schemas" / "item.py").write_text('''"""Item schemas."""
from pydantic import BaseModel


class ItemBase(BaseModel):
    title: str
    description: str | None = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int

    model_config = {"from_attributes": True}
''')

    # API routers
    (project_dir / "app" / "api" / "__init__.py").write_text('')
    (project_dir / "app" / "api" / "v1" / "__init__.py").write_text('')

    (project_dir / "app" / "api" / "v1" / "auth.py").write_text('''"""Auth endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
async def login():
    return {"message": "login endpoint"}


@router.post("/register")
async def register():
    return {"message": "register endpoint"}
''')

    (project_dir / "app" / "api" / "v1" / "items.py").write_text('''"""Items endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_items():
    return []


@router.post("/")
async def create_item():
    return {"message": "created"}
''')

    # Tests
    (project_dir / "tests" / "__init__.py").write_text('')
    (project_dir / "tests" / "api" / "__init__.py").write_text('')
    (project_dir / "tests" / "conftest.py").write_text('''"""Test configuration."""
import pytest


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)
''')

    # Pytest config
    (project_dir / "pytest.ini").write_text('''[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
''')

    # Pre-commit config
    (project_dir / ".pre-commit-config.yaml").write_text('''repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.0
    hooks:
      - id: mypy
        additional_dependencies: [types-python-jose, types-passlib]
''')

    print(f"[+] FastAPI 项目脚手架已生成: {project_dir}")
    print(f"    下一步: cd {project_dir} && python -m venv .venv && source .venv/bin/activate && pip install -e '.[dev]'")


def main():
    parser = argparse.ArgumentParser(description="FastAPI 项目脚手架生成器")
    parser.add_argument("project_name", help="项目名称")
    parser.add_argument("--dir", default=".", help="目标目录（默认当前目录）")
    args = parser.parse_args()

    project_dir = Path(args.dir) / args.project_name
    if project_dir.exists():
        print(f"[!] 目录已存在: {project_dir}")
        sys.exit(1)

    generate_structure(project_dir)


if __name__ == "__main__":
    main()
