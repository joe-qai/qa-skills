"""
Daily GitHub Discover: pick a trending repo, deep-analyze it, generate a social post.

Usage:
    python daily_discover.py [--language LANG] [--min-stars N] [--dry-run] [--output-dir DIR]

Workflow:
    1. Fetch trending repos (weekly, filtered by language if given)
    2. Pick the top candidate that passes min-stars filter
    3. Clone to .github_sandbox/<repo_name> (depth 1)
    4. Run analyze_repo.py to extract tech stack info
    5. Generate a WeChat/Zhihu-style long article (blog post)
    6. Generate a visual card image (tech stack infographic)
    7. Save all outputs to <output-dir>/<date>/<repo_name>/
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Ensure UTF-8 output on Windows (avoid GBK encoding errors with emojis/special chars)
if sys.stdout.encoding != "utf-8":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent.parent
SCRIPTS = BASE_DIR / "scripts"
GITHUB_API = SCRIPTS / "github_api.py"
ANALYZE_REPO = SCRIPTS / "analyze_repo.py"
BLOG_GEN = SCRIPTS / "blog_post_generator.py"
IMAGE_GEN = SCRIPTS / "generate_image.py"


def log(msg: str) -> None:
    print(f"[daily-discover] {msg}")


def run_github_api(args: list[str]) -> dict:
    r = subprocess.run(
        [sys.executable, str(GITHUB_API)] + args,
        capture_output=True, timeout=20,
    )
    out = r.stdout.decode("utf-8", errors="replace")
    if r.returncode != 0 or not out.strip():
        raise RuntimeError(f"github_api failed: {r.stderr.decode('utf-8', errors='replace')[:200]}")
    return json.loads(out)


def pick_trending(language: str | None, min_stars: int) -> dict:
    log("Fetching trending repos (created in last 30 days, sorted by stars)...")
    from datetime import datetime, timezone, timedelta
    date_str = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    query = f"created:>={date_str}"
    if language:
        query += f" language:{language}"
    args = ["search", query, "--sort", "stars", "--per-page", "20"]
    data = run_github_api(args)
    items = data.get("items", [])
    filtered = [r for r in items if r.get("stargazers_count", 0) >= min_stars]
    if not filtered:
        # Fallback: relax filter to top 5 anyway
        log(f"No repos >= {min_stars} stars in last 30 days, using top results instead.")
        filtered = items[:5] if items else []
    if not filtered:
        raise RuntimeError("No repos found matching the criteria.")
    return filtered[0]


def clone_repo(repo: dict, sandbox_base: Path) -> Path:
    full_name = repo["full_name"]
    repo_dir = sandbox_base / full_name.replace("/", "_")
    if repo_dir.exists():
        log(f"Reusing existing clone: {repo_dir}")
        return repo_dir
    log(f"Cloning {full_name} to {repo_dir} ...")
    clone_url = repo["clone_url"]
    r = subprocess.run(
        ["git", "clone", "--depth", "1", clone_url, str(repo_dir)],
        capture_output=True, timeout=60,
    )
    if r.returncode != 0:
        raise RuntimeError(f"git clone failed: {r.stderr.decode('utf-8', errors='replace')[:200]}")
    log(f"Clone OK ({repo_dir})")
    return repo_dir


def analyze_repo(repo_dir: Path) -> dict:
    log(f"Analyzing {repo_dir.name} ...")
    r = subprocess.run(
        [sys.executable, str(ANALYZE_REPO), str(repo_dir)],
        capture_output=True, timeout=30,
    )
    out = r.stdout.decode("utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"analyze_repo failed: {out[:200]}")
    return json.loads(out)


def generate_blog(repo_meta: dict, analysis: dict, output_dir: Path) -> Path:
    log("Generating blog post ...")
    blog_out = output_dir / "blog.md"
    r = subprocess.run(
        [sys.executable, str(BLOG_GEN),
         "--repo-meta", json.dumps(repo_meta, ensure_ascii=False),
         "--analysis", json.dumps(analysis, ensure_ascii=False),
         "--output", str(blog_out)],
        capture_output=True, timeout=30,
    )
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"blog_post_generator failed: {err[:300]}")
    log(f"Blog saved to {blog_out}")
    return blog_out


def generate_image(repo_meta: dict, analysis: dict, output_dir: Path) -> Path:
    log("Generating visual card ...")
    img_out = output_dir / "card.png"
    r = subprocess.run(
        [sys.executable, str(IMAGE_GEN),
         "--repo-meta", json.dumps(repo_meta, ensure_ascii=False),
         "--analysis", json.dumps(analysis, ensure_ascii=False),
         "--output", str(img_out)],
        capture_output=True, timeout=15,
    )
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", errors='replace')
        raise RuntimeError(f"generate_image failed: {err[:200]}")
    log(f"Image saved to {img_out}")
    return img_out


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily GitHub Discover — trending repo → deep dive → social post")
    parser.add_argument("--language", help="Filter by language (e.g. python, rust)")
    parser.add_argument("--min-stars", type=int, default=500, help="Minimum stars to consider (default: 500)")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be done, don't clone/generate")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: ./daily_output/<YYYY-MM-DD>/)")
    args = parser.parse_args()

    # Pick today's date-based output dir
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_dir = Path(args.output_dir) if args.output_dir else Path("daily_output") / today
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sandbox for clone (will be cleaned up)
    sandbox_base = Path(".github_sandbox_daily")
    sandbox_base.mkdir(exist_ok=True)

    try:
        # Step 1: Pick trending repo
        repo = pick_trending(args.language, args.min_stars)
        log(f"Selected: {repo['full_name']} ⭐{repo['stargazers_count']} — {repo.get('description', '')}")

        if args.dry_run:
            log("[dry-run] Skipping clone/analysis/image generation.")
            print(json.dumps({"selected": repo["full_name"], "stars": repo["stargazers_count"],
                              "description": repo.get("description", "")}, ensure_ascii=False, indent=2))
            return

        # Step 2: Clone
        repo_dir = clone_repo(repo, sandbox_base)

        # Step 3: Analyze
        analysis = analyze_repo(repo_dir)

        # Step 4: Generate blog post
        blog_path = generate_blog(repo, analysis, output_dir)

        # Step 5: Generate visual card
        img_path = generate_image(repo, analysis, output_dir)

        # Step 6: Save metadata for reference
        meta_out = output_dir / "meta.json"
        meta_out.write_text(json.dumps({
            "date": today,
            "repo": repo["full_name"],
            "url": repo["html_url"],
            "stars": repo["stargazers_count"],
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language", ""),
            "topics": repo.get("topics", []),
            "license": repo.get("license", {}).get("spdx_id", "") if repo.get("license") else "",
            "blog": str(blog_path),
            "image": str(img_path),
            "analysis": analysis,
        }, ensure_ascii=False, indent=2))

        log("=" * 50)
        log("Done!")
        log(f"  Blog:   {blog_path}")
        log(f"  Image:  {img_path}")
        log(f"  Meta:   {meta_out}")
        log(f"  Sandbox (can be removed): {repo_dir}")

    finally:
        # Always clean up sandbox
        if sandbox_base.exists():
            shutil.rmtree(sandbox_base, ignore_errors=True)
            log("Cleaned up .github_sandbox_daily/")


if __name__ == "__main__":
    main()
