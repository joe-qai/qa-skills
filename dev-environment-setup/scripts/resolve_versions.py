#!/usr/bin/env python3
"""
Version Resolver
Provides version selection for environments based on what's currently installed.
"""

import subprocess
import sys
from typing import Optional


# Available versions for each environment (most recent first)
AVAILABLE_VERSIONS = {
    "Python": ["3.12.8", "3.11.10", "3.10.16", "3.9.21", "3.8.20"],
    "Node.js": ["22.16.0", "20.18.0", "18.20.5", "21.7.3", "16.20.2"],
    "Go": ["1.23.4", "1.22.7", "1.21.13", "1.20.14", "1.19.13"],
    "Java": ["21.0.5", "17.0.13", "11.0.24", "22.0.2", "8u432"],
    "JMeter": ["5.6.2", "5.6.1", "5.5.1", "5.4.3", "5.4.1"],
    "Locust": ["2.32.0", "2.31.0", "2.30.0", "2.29.0", "2.28.0"],
    "Git": ["2.47.1", "2.46.0", "2.45.2", "2.44.0", "2.43.1"],
    "SVN": ["1.14.3", "1.13.1", "1.12.3", "1.11.2", "1.10.4"],
    "tidevice": ["0.13.0", "0.12.11", "0.11.0", "0.10.4", "0.9.3"],
    # Docker/WSL/HDC/ADB don't have user-selectable versions
}

# OS-specific URL templates (legacy, kept for compatibility)
URL_TEMPLATES = {
    "Python": lambda v, os_name: (
        f"https://www.python.org/ftp/python/{v}/python-{v}-amd64.exe"
        if os_name == "win32"
        else f"https://www.python.org/ftp/python/{v}/Python-{v}.tgz"
    ),
    "Node.js": lambda v, os_name: (
        f"https://nodejs.org/dist/v{v}/node-v{v}-x64.msi"
        if os_name == "win32"
        else f"https://nodejs.org/dist/v{v}/node-v{v}.tar.gz"
    ),
    "Go": lambda v, os_name: (
        f"https://go.dev/dl/go{v}.windows-amd64.msi"
        if os_name == "win32"
        else f"https://go.dev/dl/go{v}.linux-amd64.tar.gz"
    ),
    "Java": lambda v, os_name: (
        f"https://api.adoptium.net/v3/binary/latest/{v.replace('u', '.').split('.')[0]}/ga/windows/x64/jdk/hotspot/normal/eclipse"
        if "u" in v  # Hotfix format like 8u432
        else f"https://api.adoptium.net/v3/binary/release/{v}/ga/windows/x64/jdk/hotspot/normal/eclipse"
    ),
    "JMeter": lambda v, _: (
        f"https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-{v}.zip"
    ),
    "Locust": lambda *_: "https://pypi.org/project/locust/",  # pip install
    "Git": lambda v, _: (
        f"https://github.com/git-for-windows/git/releases/download/v{v}/Git-{v}-64-bit.exe"
    ),
    "SVN": lambda v, _: (
        f"https://downloads.apache.org/subversion/{v}/win64/apache-subversion-{v}-bin.zip"
    ),
    "tidevice": lambda *_: "https://pypi.org/project/tidevice/",  # pip install
}

WINGET_IDS = {
    "Python": "Python.Python.3.12",
    "Node.js": "OpenJS.NodeJS.LTS",
    "Go": "GoLang.Go",
    "Java": "EclipseAdoptium.Temurin.17.JDK",
    "Git": "Git.Git",
    "SVN": "Apache.Subversion",
}


# Download URL patterns with mirror support
OFFICIAL_SOURCES = {
    "Python": {
        "url_pattern": lambda mirror, version: f"{mirror}{version}/python-{version}-amd64.exe",
        "winget_id": "Python.Python.3.12",
    },
    "Node.js": {
        "url_pattern": lambda mirror, version: f"{mirror}v{version}/node-v{version}-x64.msi",
        "winget_id": "OpenJS.NodeJS.LTS",
    },
    "Go": {
        "url_pattern": lambda mirror, version: f"{mirror}go{version}.windows-amd64.msi",
        "winget_id": "GoLang.Go",
    },
    "Java": {
        "url_pattern": lambda mirror, version: f"{mirror}binary/release/{version}/ga/windows/x64/jdk/hotspot/normal/eclipse",
        "winget_id": "EclipseAdoptium.Temurin.17.JDK",
    },
    "JMeter": {
        "url_pattern": lambda mirror, version: f"{mirror}apache-jmeter-{version}.zip",
        "winget_id": None,
    },
    "Locust": {
        "url_pattern": None,
        "winget_id": None,
    },
    "Git": {
        "url_pattern": lambda mirror, version: f"{mirror}v{version}/Git-{version}-64-bit.exe",
        "winget_id": "Git.Git",
    },
    "SVN": {
        "url_pattern": lambda mirror, version: f"{mirror}{version}/win64/apache-subversion-{version}-bin.zip",
        "winget_id": "Apache.Subversion",
    },
    "ADB": {
        "url_pattern": lambda mirror, _: f"{mirror}platform-tools-latest-windows.zip",
        "winget_id": None,
    },
    "HDC": {
        "url_pattern": None,
        "winget_id": None,
    },
    "tidevice": {
        "url_pattern": None,
        "winget_id": None,
    },
    "Hypium": {
        "url_pattern": None,
        "winget_id": None,
    },
    "Docker": {
        "url_pattern": None,
        "winget_id": "Docker.DockerDesktop",
    },
    "WSL": {
        "url_pattern": None,
        "winget_id": None,
    },
}


def get_current_version(env_name: str) -> Optional[str]:
    """Get currently installed version of an environment."""
    version_checks = {
        "Python": lambda: run_cmd(["python", "--version"]) or run_cmd(["python3", "--version"]),
        "Node.js": lambda: run_cmd(["node", "--version"]),
        "Go": lambda: run_cmd(["go", "version"]),
        "Java": lambda: run_cmd(["java", "-version"]),
        "Git": lambda: run_cmd(["git", "--version"]),
        "SVN": lambda: run_cmd(["svn", "--version"], capture_stderr=True),
        "ADB": lambda: run_cmd(["adb", "--version"]),
        "HDC": lambda: run_cmd(["hdc", "-v"]),
        "tidevice": lambda: run_cmd(["tidevice", "--version"]),
    }
    checker = version_checks.get(env_name)
    if checker:
        try:
            output = checker()
            if output:
                return output.strip()
        except Exception:
            pass
    return None


def run_cmd(cmd: list[str], capture_stderr: bool = False) -> Optional[str]:
    """Run a command and return stdout."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            env=_get_full_env(),
            shell=(sys.platform == "win32"),
        )
        if result.returncode == 0:
            text = result.stdout if not capture_stderr else (result.stdout or result.stderr)
            return text.strip()
    except Exception:
        pass
    return None


def _get_full_env() -> dict:
    """Get environment with full PATH including common install locations."""
    env = os.environ.copy()
    # Add common dev-tool paths to help find recently installed tools
    common_paths = [
        r"E:\Test_tool_enviroment\Python\Scripts",
        r"E:\Test_tool_enviroment\NodeJs",
        r"E:\Test_tool_enviroment\Go\bin",
        r"E:\Test_tool_enviroment\Java\bin",
        r"E:\Test_tool_enviroment\JMeter\apache-jmeter-5.6.2\bin",
        r"E:\Test_tool_enviroment\Android-ADB\platform-tools",
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files\Docker\Docker\resources\bin",
    ]
    existing = env.get("PATH", "")
    for p in common_paths:
        if p not in existing:
            env["PATH"] = p + ";" + existing
    return env


def get_version_selection(env_name: str, current_version: Optional[str] = None) -> dict:
    """Return version selection info for an environment."""
    versions = AVAILABLE_VERSIONS.get(env_name, [])
    if not versions:
        return {"versions": [], "default": None, "selected": None, "strategy": "latest", "note": "无固定版本，安装最新版", "current_version": current_version}

    selected = versions[0]  # default: latest
    note = ""

    if current_version:
        # Extract major.minor from current version
        import re
        m = re.search(r"(\d+\.\d+)", current_version)
        if m:
            current_major_minor = m.group(1)
            # Check if current version is in the available list
            current_full = None
            for v in versions:
                if v.startswith(current_major_minor):
                    current_full = v
                    break
            if current_full:
                selected = current_full
                note = f"本机已安装 {current_version}，推荐保持兼容版本 {selected}"
            else:
                note = f"本机已安装 {current_version}，建议升级至最新 {versions[0]}"
    else:
        note = f"本机未安装 {env_name}，默认推荐最新版 {selected}"

    return {
        "versions": versions,
        "default": selected,
        "selected": selected,
        "current_version": current_version,
        "note": note,
        "strategy": "compatible" if current_version else "latest",
    }


def get_download_url(env_name: str, version: str) -> Optional[str]:
    """Get download URL for a specific environment and version, using mirrors."""
    from installer import get_mirrors
    info = OFFICIAL_SOURCES.get(env_name)
    if not info or not info.get("url_pattern"):
        return None
    # Try mirrors first, fall back to official
    mirrors = get_mirrors(env_name)
    for mirror in mirrors:
        try:
            url = info["url_pattern"](mirror, version)
            if url:
                return url
        except Exception:
            continue
    # Last resort: official URL
    try:
        return info["url_pattern"](mirrors[-1] if mirrors else "", version)
    except Exception:
        return None
        return info["url_pattern"](mirrors[-1] if mirrors else "", version)
    except Exception:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Version resolver for dev environments")
    parser.add_argument("env", help="Environment name (e.g. Python, Node.js, JMeter)")
    parser.add_argument("--current", help="Current installed version string")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    selection = get_version_selection(args.env, args.current)

    if args.json:
        import json
        print(json.dumps(selection, indent=2, ensure_ascii=False))
    else:
        print(f"\n{'='*50}")
        print(f"  {args.env} — Version Selection")
        print(f"{'='*50}")
        print(f"\n  {selection['note']}")
        print(f"\n  Available versions (select one or press Enter for default):")
        for i, v in enumerate(selection["versions"], 1):
            marker = " ← default" if v == selection["default"] else ""
            print(f"    [{i}] {v}{marker}")
        if selection["current_version"]:
            print(f"\n  Current: {selection['current_version']}")


if __name__ == "__main__":
    main()
