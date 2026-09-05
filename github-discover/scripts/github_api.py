"""
GitHub API wrapper with local caching.

Usage:
    python github_api.py search "<query>" [--sort stars|updated|relevance]
                                      [--lang LANGUAGE]
                                      [--page N]
                                      [--per-page N]
    python github_api.py repo "<owner>/<repo>"
    python github_api.py trends [--lang LANGUAGE] [--since daily|weekly|monthly]

Caches results in .github_cache/<query_hash>.json for 30 minutes.
Uses GITHUB_TOKEN env var if set (5000 req/hr), otherwise 60 req/hr anonymous.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

CACHE_DIR = Path(".github_cache")
CACHE_TTL = 1800  # 30 minutes

# Ensure UTF-8 output on Windows (avoid GBK encoding errors with emojis)
if sys.stdout.encoding != "utf-8":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def clean_obj(obj):
    """Recursively strip control characters from all string values in a JSON-compatible object."""
    if isinstance(obj, str):
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", obj)
    if isinstance(obj, list):
        return [clean_obj(v) for v in obj]
    if isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    return obj


def clean_json(obj):
    """Serialize to JSON after stripping control characters from string values."""
    return json.dumps(clean_obj(obj), ensure_ascii=False, indent=2)


def cache_key(query):
    return hashlib.sha256(query.encode()).hexdigest()[:16]


def get_cached(key):
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
    stat = cache_file.stat()
    if time.time() - stat.st_mtime > CACHE_TTL:
        return None
    with open(cache_file, encoding="utf-8") as f:
        return json.load(f)


def set_cached(key, data):
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def github_request(url, headers=None):
    token = os.environ.get("GITHUB_TOKEN", "")
    req_headers = {"Accept": "application/vnd.github+json"}
    if token:
        req_headers["Authorization"] = f"Bearer {token}"
        req_headers["X-GitHub-Api-Version"] = "2022-11-28"
    if headers:
        req_headers.update(headers)

    req = Request(url, headers=req_headers)
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        body = ""
        try:
            body = e.read().decode(errors="replace")
        except Exception:
            pass
        if e.code == 403 and ("rate limit" in body.lower() or "rate limited" in body.lower()):
            print(json.dumps({"error": "GitHub API rate limit exceeded. Set GITHUB_TOKEN env var.", "rate_limited": True}, ensure_ascii=False))
            sys.exit(1)
        raise
    except URLError as e:
        print(json.dumps({"error": f"Network error: {e.reason}"}, ensure_ascii=False))
        sys.exit(1)


def cmd_search(args):
    q = args.query
    sort = getattr(args, "sort", "relevance")
    lang = getattr(args, "lang", None)
    page = getattr(args, "page", 1)
    per_page = getattr(args, "per_page", 20)

    parts = [q]
    if lang:
        parts.append(f"language:{lang}")
    cache_query = "+".join(parts) + f"|{sort}|{page}"
    key = cache_key(cache_query)

    cached = get_cached(key)
    if cached:
        print(clean_json(cached))
        return

    url = f"https://api.github.com/search/repositories?q={quote(q)}&sort={sort}&page={page}&per_page={per_page}"
    if lang:
        url += f"&language={lang}"

    data = github_request(url)
    set_cached(key, data)
    print(clean_json(data))


def cmd_repo(args):
    repo = args.repo
    key = cache_key(f"repo:{repo}")

    cached = get_cached(key)
    if cached:
        print(clean_json(cached))
        return

    url = f"https://api.github.com/repos/{repo}"
    data = github_request(url)
    set_cached(key, data)
    print(clean_json(data))


def cmd_trends(args):
    lang = getattr(args, "lang", None)
    since = getattr(args, "since", "weekly")
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(since, 7)
    date_str = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    key = cache_key(f"trends:{lang}:{since}")

    cached = get_cached(key)
    if cached:
        print(clean_json(cached))
        return

    url = f"https://api.github.com/search/repositories?q=created:>={date_str}&sort=stars&order=desc&per_page=25"
    if lang:
        url += f"&language={lang}"

    data = github_request(url)
    set_cached(key, data)
    print(clean_json(data))


def main():
    parser = argparse.ArgumentParser(description="GitHub API wrapper with caching")
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search repositories")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--sort", choices=["stars", "updated", "relevance"], default="relevance")
    p_search.add_argument("--lang", help="Filter by language")
    p_search.add_argument("--page", type=int, default=1)
    p_search.add_argument("--per-page", type=int, default=20)

    p_repo = sub.add_parser("repo", help="Get single repo metadata")
    p_repo.add_argument("repo", help="Owner/repo")

    p_trends = sub.add_parser("trends", help="Trending repos by time period")
    p_trends.add_argument("--lang", help="Filter by language")
    p_trends.add_argument("--since", choices=["daily", "weekly", "monthly"], default="weekly")

    args = parser.parse_args()
    {"search": cmd_search, "repo": cmd_repo, "trends": cmd_trends}[args.command](args)


if __name__ == "__main__":
    main()
