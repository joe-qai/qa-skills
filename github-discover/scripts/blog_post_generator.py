"""
Generate a WeChat/Zhihu-style long article from repo metadata + analysis.

Usage:
    python blog_post_generator.py \\
        --repo-meta <json_string_or_path> \\
        --analysis <json_string_or_path> \\
        --output <path.md>

Tone: 网感风 — engaging, opinionated, with hooks, insights, and a clear takeaway.
Output: Markdown suitable for WeChat Official Account or Zhihu (HTML export later).
"""

import argparse
import json
import sys
from datetime import datetime, timezone


def load_json(arg: str):
    """Accept either a file path or inline JSON."""
    if arg.startswith("{") or arg.startswith("["):
        return json.loads(arg)
    with open(arg, encoding="utf-8") as f:
        return json.load(f)


def extract_deps(analysis: dict) -> list[dict]:
    """Parse dependency info from analyze_repo output."""
    deps = []
    for dep_file in analysis.get("dependencies", []):
        for name, version in dep_file.get("dependencies", {}).items():
            deps.append({"name": name, "version": version, "source": dep_file.get("file", "")})
    return deps[:20]  # top 20


def categorize_deps(deps: list[dict]) -> dict:
    """Group deps into categories."""
    categories = {"框架": [], "工具": [], "测试": [], "其他": []}
    framework_keywords = {"fastapi", "flask", "django", "starlette", "axios", "react", "vue",
                          "next", " Express", "actix", "tokio", "axum", "spring", "gin", "laravel",
                          "rails", "numpy", "pandas", "torch", "tensorflow", "langchain", "crewai",
                          "pytest", "jest", "mocha", "cargo", "npm", "yarn", "poetry"}
    test_keywords = {"pytest", "unittest", "jest", "mocha", "cypress", "playwright",
                     "selenium", "nox", "tox", "coverage"}
    tool_keywords = {"black", "ruff", "mypy", "pre-commit", "docker", "github-actions",
                     "semgrep", "sonarqube"}

    for d in deps:
        name_lower = d["name"].lower()
        if any(k in name_lower for k in framework_keywords):
            categories["框架"].append(d)
        elif any(k in name_lower for k in test_keywords):
            categories["测试"].append(d)
        elif any(k in name_lower for k in tool_keywords):
            categories["工具"].append(d)
        else:
            categories["其他"].append(d)
    return categories


def make_hook(repo: dict, deps_cat: dict) -> str:
    """Create an attention-grabbing opening hook."""
    stars = repo.get("stargazers_count", 0)
    desc = repo.get("description", "一个值得关注的项目")
    lang = repo.get("language", "")
    topics = repo.get("topics", [])

    # Build hook based on star count tier
    if stars >= 50000:
        prestige = "现象级"
    elif stars >= 10000:
        prestige = "火爆"
    elif stars >= 5000:
        prestige = "热门"
    else:
        prestige = "潜力"

    top_topic = topics[0] if topics else lang
    return (
        f"最近刷到这个项目的时候我愣了一下——{stars:,} star 的 {repo['full_name']}，"
        f"居然把 {top_topic} 玩出了新花样。\n\n"
        f"{desc}。"
    )


def make_tech_stack_section(deps_cat: dict) -> str:
    """Write the tech stack section with commentary."""
    lines = ["## 🔧 技术栈拆解\n"]

    for cat_name, items in deps_cat.items():
        if not items:
            continue
        lines.append(f"### {cat_name}\n")
        for item in items[:5]:
            ver = item.get("version", "")
            lines.append(f"- **{item['name']}** `{"、}".join([ver])}`")
        lines.append("")

    return "\n".join(lines) if lines[-1] != "\n" else "\n".join(lines.rstrip())


def make_takeaway(repo: dict, analysis: dict, deps_cat: dict) -> str:
    """Write the 'why you should care' conclusion."""
    stars = repo.get("stargazers_count", 0)
    updated = repo.get("updated_at", "")[:10]
    language = repo.get("language", "")
    topics = repo.get("topics", [])

    # Find interesting signal
    signals = []
    if stars >= 10000:
        signals.append(f"⭐ {stars:,} star，属于这个领域的第一梯队")
    if updated:
        signals.append(f"📅 最近更新 {updated}，说明还在活跃维护")
    if language:
        signals.append(f"💻 主要用 {language} 写的")
    if topics:
        signals.append(f"🏷️  被打上了 {', '.join(topics[:3])} 等标签")

    # Check for CI/CD maturity
    ci_files = analysis.get("ci_files", [])
    if ci_files:
        signals.append(f"🔄 CI/CD 配置完整（{len(ci_files)} 个 workflow 文件）")

    # Check code quality tools
    quality = analysis.get("code_quality_tools", [])
    if quality:
        signals.append(f"🛡️  代码质量工具链齐全：{', '.join(quality[:3])}")

    signal_text = "；".join(signals)

    return (
        f"\n\n## 💡 值不值得看？\n\n"
        f"简单说：{signal_text}。\n\n"
        f"如果你正在关注 {', '.join(topics[:2]) if topics else language} 方向，"
        f"这个项目值得加入你的 Star 列表，或者 clone 下来当学习参考。\n\n"
        f"> 📌 原文链接：{repo.get('html_url', '')}\n"
    )


def generate_blog(repo: dict, analysis: dict) -> str:
    """Generate the full blog post."""
    deps = extract_deps(analysis)
    deps_cat = categorize_deps(deps)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Build sections
    title = f"今日 GitHub 热榜：{repo['full_name']} 凭什么火了？"
    intro = f"\n\n*{now} · 每日开源项目深挖*\n\n"

    hook = make_hook(repo, deps_cat)
    tech_section = make_tech_stack_section(deps_cat)
    takeaway = make_takeaway(repo, analysis, deps_cat)

    # Directory structure insight
    structure = analysis.get("directory_structure", {})
    if structure:
        top_dirs = list(structure.items())[:6]
        dir_text = "\n".join(f"  {name}/  （{count} 个子项）" for name, count in top_dirs)
        structure_section = f"\n\n## 📁 项目结构\n\n```\n{dir_text}\n```\n"
    else:
        structure_section = ""

    readme_excerpt = analysis.get("readme_excerpt", "")[:300]
    if readme_excerpt:
        readme_section = f"\n\n## 📖 项目定位\n\n{readme_excerpt}\n"
    else:
        readme_section = ""

    post = f"""# {title}
{intro}
{hook}
{readme_section}
{structure_section}
{tech_section}
{takeaway}
---
*这是 [github-discover](https://github.com/your-org/github-discover) 每日开源项目深挖系列的第 {today_num()} 篇。*
"""
    return post


def today_num() -> int:
    """Return day-of-year for serial numbering."""
    return datetime.now(timezone.utc).timetuple().tm_yday


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a WeChat/Zhihu-style blog post from repo data")
    parser.add_argument("--repo-meta", required=True, help="Repo metadata JSON (file path or inline)")
    parser.add_argument("--analysis", required=True, help="Analysis JSON (file path or inline)")
    parser.add_argument("--output", "-o", required=True, help="Output .md file path")
    args = parser.parse_args()

    repo = load_json(args.repo_meta)
    analysis = load_json(args.analysis)

    post = generate_blog(repo, analysis)

    out = open(args.output, "w", encoding="utf-8")
    out.write(post)
    out.close()


if __name__ == "__main__":
    main()
