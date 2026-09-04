#!/usr/bin/env python3
"""
Django Project Scaffold Generator
Creates a new Django project with recommended structure and tooling.
"""

import argparse
import os
import sys
import shutil
from pathlib import Path


TEMPLATES = {
    "basic": {
        "name": "basic",
        "description": "基础 Django 项目",
        "packages": ["django", "djangorestframework", "psycopg2-binary", "dotenv", "gunicorn"],
    },
    "api": {
        "name": "api",
        "description": "Django REST API 项目（含 DRF）",
        "packages": ["django", "djangorestframework", "django-cors-headers", "psycopg2-binary", "dotenv", "gunicorn", "celery", "redis"],
    },
    "fullstack": {
        "name": "fullstack",
        "description": "前后端分离项目（Django + Vue）",
        "packages": ["django", "djangorestframework", "django-cors-headers", "psycopg2-binary", "dotenv", "gunicorn", "djoser"],
    },
}


def generate_structure(project_dir: Path, template: str):
    """Generate project directory structure and files."""
    structure = {
        ".env.example": 'DJANGO_SECRET_KEY=your-secret-key-here\nDJANGO_DEBUG=True\nDATABASE_URL=postgres://user:pass@localhost:5432/dbname\nREDIS_URL=redis://localhost:6379/0\n',
        ".gitignore": '''__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
*.sqlite3
*.db
node_modules/
dist/
build/
.DS_Store
*.orig
coverage.xml
*.cover
.html-report/
.''',
        "manage.py": '''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
''',
        "requirements.txt": '''django>=5.2
djangorestframework>=3.16
django-cors-headers>=4.6
psycopg2-binary>=2.9
python-dotenv>=1.0
gunicorn>=23.0
''',
        "requirements-dev.txt": '''-r requirements.txt
pytest>=8.0
pytest-django>=4.9
pytest-cov>=6.0
black>=24.0
isort>=6.0
flake8>=7.0
mypy>=1.0
pre-commit>=4.0
factory-boy>=3.3
''',
    }

    # Template-specific additions
    if template in ("api", "fullstack"):
        structure["requirements.txt"] += 'celery>=5.4\nredis>=5.2\n'
    if template == "fullstack":
        structure["requirements.txt"] += 'djoser>=2.3\n'

    # Create directories
    dirs = [
        "config",
        "apps",
        "apps/users",
        "apps/users/migrations",
        "static",
        "media",
        "tests",
        ".github/workflows",
    ]
    for d in dirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)
        # Create empty __init__.py for Python packages
        init_file = project_dir / d / "__init__.py"
        if d not in ("static", "media", ".github/workflows"):
            init_file.touch()

    # Write base files
    (project_dir / "config" / "__init__.py").touch()
    (project_dir / "apps" / "__init__.py").touch()
    (project_dir / "tests" / "__init__.py").touch()

    # Write template files
    (project_dir / "config" / "settings.py").write_text('''"""
Django settings for {{project_name}} project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-production")
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    # Local apps
    "apps.users",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "db"),
        "USER": os.getenv("DB_USER", "user"),
        "PASSWORD": os.getenv("DB_PASS", "pass"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF settings
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# CORS
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOW_CREDENTIALS = True
''')

    (project_dir / "config" / "urls.py").write_text('''"""
URL configuration for {{project_name}} project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls")),
    path("api/", include("apps.users.urls")),
]
''')

    (project_dir / "config" / "wsgi.py").write_text('''"""
WSGI config for {{project_name}} project.
"""
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
''')

    (project_dir / "config" / "asgi.py").write_text('''"""
ASGI config for {{project_name}} project.
"""
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()
''')

    # GitHub Actions CI
    (project_dir / ".github" / "workflows" / "ci.yml").write_text('''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pip install -r requirements-dev.txt
      - run: python manage.py migrate --settings=config.settings
      - run: python manage.py test --settings=config.settings
''')

    print(f"[+] Django 项目脚手架已生成: {project_dir}")
    print(f"    模板: {TEMPLATES[template]['description']}")
    print(f"    下一步: cd {project_dir} && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt")


def main():
    parser = argparse.ArgumentParser(description="Django 项目脚手架生成器")
    parser.add_argument("project_name", help="项目名称")
    parser.add_argument("--dir", default=".", help="目标目录（默认当前目录）")
    parser.add_argument(
        "--template",
        choices=list(TEMPLATES.keys()),
        default="api",
        help="项目模板类型（默认: api）",
    )
    args = parser.parse_args()

    project_dir = Path(args.dir) / args.project_name
    if project_dir.exists():
        print(f"[!] 目录已存在: {project_dir}")
        sys.exit(1)

    generate_structure(project_dir, args.template)


if __name__ == "__main__":
    main()
