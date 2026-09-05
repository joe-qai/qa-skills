"""
Deep tech-stack analysis for a cloned GitHub repository.

Usage:
    python analyze_repo.py <repo_path> [--output report.md]

Produces a structured markdown report covering:
  - Project overview (meta from GitHub API or filesystem)
  - Dependency configuration (package files)
  - Directory structure
  - CI/CD and engineering practices
  - License and contribution guidelines
  - Quick start commands (from README)
  - Learning recommendations
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# File parsers
# ---------------------------------------------------------------------------

def parse_package_json(repo: Path) -> dict:
    pkg = repo / "package.json"
    if not pkg.exists():
        return {}
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
        deps = {
            **{k: v for k, v in data.get("dependencies", {}).items()},
            **{k: v for k, v in data.get("devDependencies", {}).items()},
            **{k: v for k, v in data.get("peerDependencies", {}).items()},
        }
        return {"file": "package.json", "dependencies": deps, "scripts": data.get("scripts", {})}
    except Exception:
        return {}


def parse_pyproject(repo: Path) -> dict:
    pp = repo / "pyproject.toml"
    if not pp.exists():
        # fallback: requirements.txt
        req = repo / "requirements.txt"
        if req.exists():
            deps = {}
            for line in req.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    m = re.match(r"^([a-zA-Z0-9_-]+)\s*(?:[<>=!~]\s*.+)?", line)
                    if m:
                        deps[m.group(1)] = line
            return {"file": "requirements.txt", "dependencies": deps}
        return {}
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    data = tomllib.loads(pp.read_text(encoding="utf-8"))
    deps: dict = {}
    for section in ("dependencies", "dev-dependencies", "optional-dependencies"):
        for k, v in data.get("project", {}).get(section.replace("-", "_", 1), {}).items():
            deps[k] = str(v)
    return {"file": "pyproject.toml", "dependencies": deps}


def parse_cargo_toml(repo: Path) -> dict:
    ct = repo / "Cargo.toml"
    if not ct.exists():
        return {}
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    data = tomllib.loads(ct.read_text(encoding="utf-8"))
    deps = {}
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        sec_data = data.get("package", {}) if section == "package" else data.get(section, {})
        for k, v in sec_data.items():
            if isinstance(v, dict):
                deps[k] = v.get("version", "*")
            else:
                deps[k] = str(v)
    return {"file": "Cargo.toml", "dependencies": deps}


def parse_go_mod(repo: Path) -> dict:
    gm = repo / "go.mod"
    if not gm.exists():
        return {}
    deps = {}
    in_deps = False
    for line in gm.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line == "require (":
            in_deps = True
            continue
        if line == ")":
            in_deps = False
            continue
        if in_deps:
            parts = line.split()
            if len(parts) >= 2:
                deps[parts[0]] = parts[1]
        elif line.startswith("require ") and " (" not in line:
            parts = line.split()
            if len(parts) >= 3:
                deps[parts[1]] = parts[2]
    return {"file": "go.mod", "dependencies": deps}


def parse_pom(repo: Path) -> dict:
    pom = repo / "pom.xml"
    if not pom.exists():
        return {}
    text = pom.read_text(encoding="utf-8")
    deps = {}
    for m in re.finditer(r"<dependency>\s*<groupId>([^<]+)</groupId>\s*<artifactId>([^<]+)</artifactId>\s*<version>([^<]*)</version>", text):
                    deps[f"{m.group(1)}:{m.group(2)}"] = m.group(3)
    return {"file": "pom.xml", "dependencies": deps} if deps else {}


# ---------------------------------------------------------------------------
# Structure analysis
# ---------------------------------------------------------------------------

def scan_structure(repo: Path) -> dict:
    dirs = {}
    for child in sorted(repo.iterdir()):
        if child.is_dir() and not child.name.startswith((".", "__")):
            sub_count = sum(1 for _ in child.iterdir())
            dirs[child.name] = sub_count
    return dirs


def find_ci_files(repo: Path) -> list[str]:
    ci = []
    paths = [
        repo / ".github" / "workflows",
        repo / "Jenkinsfile",
        repo / ".gitlab-ci.yml",
        repo / ".circleci",
        repo / "azure-pipelines.yml",
    ]
    for p in paths:
        if p.is_dir():
            ci.extend(f".github/workflows/{f.name}" for f in p.glob("*.yml") if f.is_file())
        elif p.exists():
            ci.append(p.name)
    return ci


def find_code_quality(repo: Path) -> list[str]:
    checks = []
    for name in ["ruff.toml", "pyproject.toml", "eslint.config.js", "eslint.config.mjs",
                 ".prettierrc", ".pre-commit-config.yaml", "mypy.ini", "setup.cfg",
                 "codecov.yml", ".coveragerc"]:
        if (repo / name).exists():
            checks.append(name)
    return checks


# ---------------------------------------------------------------------------
# README extraction
# ---------------------------------------------------------------------------

def extract_readme(repo: Path) -> dict:
    candidates = ["README.md", "README.rst", "README.txt",
                  "README.zh-CN.md", "README.zh-TW.md", "README.cn.md"]
    for name in candidates:
        p = repo / name
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")[:3000]
            return {"file": name, "content": text}
    return {}


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def analyze(repo_path: str, output_path: str | None) -> None:
    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        print(json.dumps({"error": f"Directory not found: {repo_path}"}), file=sys.stderr)
        sys.exit(1)

    repo_name = repo.name

    # Parse dependencies
    dep_parsers = [parse_pyproject, parse_cargo_toml, parse_package_json, parse_go_mod, parse_pom]
    dep_results = []
    for parser in dep_parsers:
        result = parser(repo)
        if result:
            dep_results.append(result)
            break  # first match wins for display; can extend to show all

    # Structure
    structure = scan_structure(repo)
    ci_files = find_ci_files(repo)
    code_quality = find_code_quality(repo)
    readme = extract_readme(repo)

    report = {
        "repo_name": repo_name,
        "repo_path": str(repo),
        "dependencies": dep_results,
        "directory_structure": structure,
        "ci_files": ci_files,
        "code_quality_tools": code_quality,
        "readme_excerpt": readme.get("content", "")[:1500],
        "readme_file": readme.get("file"),
    }

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report saved to {out}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a cloned GitHub repository's tech stack")
    parser.add_argument("repo_path", help="Path to the cloned repository")
    parser.add_argument("--output", "-o", help="Output path for the report (markdown or json)")
    args = parser.parse_args()
    analyze(args.repo_path, args.output)


if __name__ == "__main__":
    main()
