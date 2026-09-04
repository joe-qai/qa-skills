#!/usr/bin/env python3
"""
Pre-Install Confirmation Builder
Generates a structured installation plan for user review and confirmation.
Uses dynamic version resolution (resolve_versions.py) — no hardcoded versions.
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Add scripts directory to path for imports
_SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPTS_DIR))

from resolve_versions import (
    AVAILABLE_VERSIONS,
    URL_TEMPLATES,
    WINGET_IDS,
    get_download_url,
    get_version_selection,
)
from installer import TIMEOUTS, get_timeout_for_tool


# Dependency map: env_name -> list of (dependency_name, required_for_install)
DEPENDENCIES = {
    "Docker": [("WSL", False)],
    "JMeter": [("Java", True)],
    "Locust": [("Python", True)],
    "tidevice": [("Python", True)],
    "Hypium": [("Node.js", True)],
}

# Dependency ordering (topological sort) — shallower deps first
DEPENDENCY_ORDER = [
    "Python", "Node.js", "Go", "Java", "Git", "SVN", "WSL",
    "ADB", "HDC", "Docker", "JMeter", "Locust", "tidevice", "Hypium",
]

# OS support per environment
OS_SUPPORT = {
    "Python":          {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "Node.js":         {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "Go":              {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "Java":            {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "Docker":          {"supported": ["win32", "darwin"],           "condition": "Windows 需 WSL2（编号 8）"},
    "Git":             {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "SVN":             {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "WSL":             {"supported": ["win32"],                     "condition": "仅 Windows；macOS/Linux 原生支持容器"},
    "JMeter":          {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "Locust":          {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "ADB":             {"supported": ["win32", "darwin", "linux"],  "condition": ""},
    "HDC":             {"supported": ["win32", "darwin"],           "condition": "需华为开发者账号授权；Linux 不支持"},
    "tidevice":        {"supported": ["win32", "darwin"],           "condition": "Windows 支持有限（需 libimobiledevice），推荐 macOS"},
    "Hypium":          {"supported": ["win32", "darwin"],           "condition": "鸿蒙测试框架；Linux 不支持"},
}

# Environment variable config per environment
ENV_VAR_CONFIG = {
    "Python": [
        {"name": "PYTHON_HOME", "scope": "Machine", "value_template": "{base_dir}/Python"},
        {"name": "Path", "scope": "Machine", "value_template": "{base_dir}/Python;{base_dir}/Python\\Scripts"},
    ],
    "Node.js": [
        {"name": "Path", "scope": "Machine", "value_template": "{base_dir}/NodeJs"},
    ],
    "Go": [
        {"name": "GOROOT", "scope": "Machine", "value_template": "{base_dir}/Go"},
        {"name": "Path", "scope": "Machine", "value_template": "{base_dir}/Go\\bin"},
    ],
    "Java": [
        {"name": "JAVA_HOME", "scope": "Machine", "value_template": "{base_dir}/Java"},
        {"name": "Path", "scope": "Machine", "value_template": "{base_dir}/Java\\bin"},
    ],
    "Docker": [],
    "Git": [],
    "SVN": [
        {"name": "Path", "scope": "Machine", "value_template": "{base_dir}/SVN\\bin"},
    ],
    "WSL": [],
    "JMeter": [
        {"name": "Path", "scope": "Machine", "value_template": "{base_dir}/JMeter/{version}\\bin"},
        {"name": "JMETER_HOME", "scope": "Machine", "value_template": "{base_dir}/JMeter/{version}"},
    ],
    "Locust": [],
    "ADB": [
        {"name": "Path", "scope": "Machine", "value_template": "{base_dir}/Android-ADB/platform-tools"},
    ],
    "HDC": [
        {"name": "Path", "scope": "Machine", "value_template": "{base_dir}/HDC"},
    ],
    "tidevice": [],
    "Hypium": [],
}

# Network domains per environment
NETWORK_DOMAINS = {
    "Python":      ["python.org", "www.python.org"],
    "Node.js":     ["nodejs.org", "npmjs.org"],
    "Go":          ["go.dev"],
    "Java":        ["adoptium.net", "api.adoptium.net"],
    "Docker":      ["docker.com"],
    "Git":         ["github.com"],
    "SVN":         ["downloads.apache.org"],
    "WSL":         ["microsoft.com"],
    "JMeter":      ["archive.apache.org"],
    "Locust":      ["pypi.org"],
    "ADB":         ["dl.google.com"],
    "HDC":         ["huawei.com"],
    "tidevice":    ["pypi.org"],
    "Hypium":      ["registry.npmjs.org"],
}

# Risk level per environment
RISK_LEVEL = {
    "Python": "L1", "Node.js": "L1", "Go": "L1", "Java": "L1",
    "Docker": "L1", "Git": "L0", "SVN": "L0", "WSL": "L1",
    "JMeter": "L1", "Locust": "L1", "ADB": "L0", "HDC": "L0",
    "tidevice": "L1", "Hypium": "L1",
}

# Install size estimates in MB (conservative, before 20% margin)
SIZE_ESTIMATES = {
    "Python": 250, "Node.js": 180, "Go": 150, "Java": 300,
    "Docker": 800, "Git": 100, "SVN": 20, "WSL": 500,
    "JMeter": 120, "Locust": 5, "ADB": 25, "HDC": 15,
    "tidevice": 5, "Hypium": 10,
}


def get_system_drive() -> str:
    drives = []
    for i in range(65, 91):
        letter = f"{chr(i)}:\\"
        if os.path.exists(letter):
            drives.append(letter)
    return drives[0] if drives else "C:\\"


def get_free_space_mb(drive: str) -> int:
    """Get free space in MB for a drive. Returns 0 on failure."""
    try:
        import ctypes
        drive_root = drive.rstrip("\\") + "\\"
        free_bytes = ctypes.c_longlong()
        success = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
            drive_root, None, None, ctypes.byref(free_bytes)
        )
        if success and free_bytes.value > 0:
            return int(free_bytes.value // (1024 * 1024))
    except Exception:
        pass
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"(Get-PSDrive -Name '{drive.rstrip(chr(58))}' -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Free)/1MB"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            val = int(float(result.stdout.strip()))
            if val > 0:
                return val
    except Exception:
        pass
    return 0


def resolve_dependencies(selected: list[str]) -> list[str]:
    """Resolve full dependency closure with topological ordering."""
    resolved = set()
    queue = list(selected)
    while queue:
        name = queue.pop(0)
        if name in resolved:
            continue
        resolved.add(name)
        for dep_name, required in DEPENDENCIES.get(name, []):
            if dep_name not in resolved:
                queue.append(dep_name)
    return [name for name in DEPENDENCY_ORDER if name in resolved]


def build_plan(selected_envs: list[str], base_dir: str, existing: dict,
               version_overrides: dict = None) -> dict:
    """Build a structured installation plan for user confirmation."""
    current_os = sys.platform
    version_overrides = version_overrides or {}

    plan = {
        "base_dir": base_dir,
        "system_drive": get_system_drive(),
        "current_os": current_os,
        "free_space_mb": get_free_space_mb(get_system_drive()),
        "items": [],
        "total_estimate_mb": 0,
        "requires_network": False,
        "network_domains": set(),
        "env_var_changes": [],
        "risks": [],
        "os_incompatible": [],
        "version_notes": [],
    }

    ordered_envs = resolve_dependencies(selected_envs)

    for env_name in ordered_envs:
        os_info = OS_SUPPORT.get(env_name)
        if not os_info:
            continue

        # OS compatibility check
        if current_os not in os_info["supported"]:
            plan["os_incompatible"].append({
                "name": env_name,
                "condition": os_info["condition"] or f"不支持当前 OS: {current_os}",
            })
            continue

        is_installed = existing.get(env_name, {}).get("found", False)
        is_local = existing.get(env_name, {}).get("local_path") is not None

        # Determine version
        current_ver_str = existing.get(env_name, {}).get("version", "")
        user_version = version_overrides.get(env_name)

        if user_version:
            selected_version = user_version
            version_note = f"用户指定版本: {selected_version}"
        elif is_installed and current_ver_str:
            selection = get_version_selection(env_name, current_ver_str)
            selected_version = selection.get("selected") or selection.get("default")
            version_note = selection.get("note", "")
        else:
            selection = get_version_selection(env_name)
            selected_version = selection.get("selected") or selection.get("default")
            version_note = selection.get("note", "")

        # For environments without fixed versions (ADB, Docker, etc.)
        if not selected_version:
            selected_version = "latest"
            version_note = version_note or "安装最新版"

        plan["version_notes"].append({"env": env_name, "note": version_note})

        # Build URL — use mirror-aware resolver from resolve_versions
        url = None
        if not is_local:
            from resolve_versions import get_download_url
            url = get_download_url(env_name, selected_version)

        estimate = SIZE_ESTIMATES.get(env_name, 100)
        estimate_with_margin = int(estimate * 1.2)

        # Build install directory (some tools embed version in path)
        install_dir = f"{base_dir}/{env_name}"
        if env_name == "JMeter":
            install_dir = f"{base_dir}/JMeter/{selected_version}"
        elif env_name == "Android-ADB":
            install_dir = f"{base_dir}/Android-ADB/platform-tools"

        # Build env var values
        env_vars = []
        for ev in ENV_VAR_CONFIG.get(env_name, []):
            value = ev["value_template"].format(base_dir=base_dir, version=selected_version)
            env_vars.append({"name": ev["name"], "scope": ev["scope"], "value": value})

        item = {
            "name": env_name,
            "version": selected_version,
            "installed": is_installed,
            "source": "LOCAL" if is_local else "ONLINE",
            "url": url,
            "install_dir": install_dir,
            "estimated_mb": estimate_with_margin,
            "env_vars": env_vars,
            "network_domains": NETWORK_DOMAINS.get(env_name, []),
            "risk": RISK_LEVEL.get(env_name, "L1"),
            "os_condition": os_info["condition"],
            "dependencies": [],
            "version_note": version_note,
            "timeout_seconds": get_timeout_for_tool(env_name),
            "retries": 3,
            "install_methods": _get_install_methods(env_name),
            "mirrors": _get_mirror_urls(env_name)[:1],  # show primary only in plan
        }

        # Dependencies
        for dep_name, required in DEPENDENCIES.get(env_name, []):
            dep_installed = existing.get(dep_name, {}).get("found", False)
            dep_blocked = any(ib["name"] == dep_name for ib in plan["os_incompatible"])
            if dep_blocked:
                item["dependencies"].append({
                    "name": dep_name, "installed": False,
                    "status": f"BLOCKED ({os_info.get('condition', '')})",
                    "required": required,
                })
            else:
                item["dependencies"].append({
                    "name": dep_name, "installed": dep_installed,
                    "status": "OK" if dep_installed else "NEEDS_INSTALL",
                    "required": required,
                })

        # Check if blocked by missing required dependency
        blocked_deps = [d for d in item["dependencies"] if "BLOCKED" in d["status"] and d["required"]]
        if blocked_deps:
            plan["os_incompatible"].append({
                "name": env_name,
                "condition": f"依赖 {', '.join(d['name'] for d in blocked_deps)} 不可用",
            })
            continue

        plan["items"].append(item)
        plan["total_estimate_mb"] += estimate_with_margin

        if not is_installed and not is_local:
            plan["requires_network"] = True
            plan["network_domains"].update(item["network_domains"])

        for ev in env_vars:
            plan["env_var_changes"].append({
                "env": env_name, "var_name": ev["name"],
                "scope": ev["scope"], "value": ev["value"],
            })

        if item["risk"] in ("L1", "L2"):
            plan["risks"].append(f"{env_name}: {item['risk']}")

    plan["network_domains"] = list(plan["network_domains"])
    return plan


def _get_install_methods(env_name: str) -> list[str]:
    """Return list of install methods attempted in order."""
    methods = []
    os_name = sys.platform
    if os_name == "win32":
        methods.append("winget")
        methods.append("download+msiexe")
    elif os_name == "darwin":
        methods.append("brew")
    else:
        methods.append("apt")
        methods.append("snap")
    return methods


def _get_mirror_urls(env_name: str) -> list[str]:
    """Return ordered list of mirror URLs for an environment."""
    from installer import get_mirrors
    mirrors = get_mirrors(env_name)
    # Build full URLs using the URL template from resolve_versions
    result = []
    version = None
    # Find version from the loop context — not available here, return base mirrors
    for m in mirrors:
        result.append(m)
    return result


def print_plan(plan: dict):
    """Print the installation plan in human-readable format."""
    print("\n" + "=" * 70)
    print("  PRE-INSTALLATION CONFIRMATION PLAN")
    print("=" * 70)

    print(f"\n  Current OS:     {plan['current_os']}")
    print(f"  Base install:   {plan['base_dir']}")
    print(f"  System drive:   {plan['system_drive']}")
    free_mb = plan['free_space_mb']
    needed_mb = plan['total_estimate_mb']
    has_enough = free_mb >= needed_mb and free_mb > 0
    if free_mb == 0:
        space_msg = "[UNKNOWN — cannot detect disk space, will refuse install]"
    else:
        space_msg = f"{free_mb:,} MB"
    print(f"  Free space:     {space_msg}  |  Estimated needed: {needed_mb:,} MB  {'[OK]' if has_enough else '[INSUFFICIENT]'}")

    # OS incompatible items
    if plan["os_incompatible"]:
        print("\n" + "-" * 70)
        print("  OS Incompatible (SKIP)")
        print("-" * 70)
        for item in plan["os_incompatible"]:
            print(f"    [SKIP] {item['name']:<15} — {item['condition']}")

    print("\n" + "-" * 70)
    print("  Environment Details")
    print("-" * 70)

    for item in plan["items"]:
        status = "[INSTALLED]" if item["installed"] else ("[LOCAL]" if item["source"] == "LOCAL" else "[ONLINE]")
        ver_tag = f"  v{item['version']}" if item.get("version") else ""
        print(f"\n  [{item['name']}] {status}{ver_tag}")
        print(f"    Source:       {item['source']}")
        if item.get("url"):
            print(f"    Download URL: {item['url']}")
        print(f"    Install dir:  {item['install_dir']}")
        print(f"    Est. size:    {item['estimated_mb']} MB (+20% margin)")
        print(f"    Timeout:      ~{item.get('timeout_seconds', 300)}s")
        print(f"    Retries:      {item.get('retries', 3)} attempts per mirror × 3 mirrors")
        print(f"    Risk:         {item['risk']}")
        print(f"    Methods:      {' → '.join(item.get('install_methods', ['manual']))}")
        mirrors = item.get('mirrors', [])
        if mirrors:
            print(f"    Mirrors:      {mirrors[0][:40]}... (×2 backups)")
        if item.get("version_note"):
            print(f"    Note:         {item['version_note']}")
        if item.get("os_condition"):
            print(f"    OS note:      {item['os_condition']}")

        # Dependencies
        if item["dependencies"]:
            dep_strs = [f"{d['name']}({d['status']})" for d in item["dependencies"]]
            print(f"    Dependencies: {', '.join(dep_strs)}")

        # Env vars
        if item["env_vars"]:
            print(f"    Env vars to set:")
            for ev in item["env_vars"]:
                print(f"      {ev['name']} ({ev['scope']}) = {ev['value']}")

    # Network summary
    if plan["requires_network"]:
        print(f"\n  Network access required: YES")
        print(f"  Domains to access: {', '.join(plan['network_domains'])}")
        print(f"  NOTE: Downloaded files will be verified with SHA-256 before installation.")
    else:
        print(f"\n  Network access required: NO (all packages available locally)")

    # Space check — BLOCK if insufficient
    if not has_enough and free_mb > 0:
        print(f"\n  [BLOCKED] Insufficient space on {plan['system_drive']}.")
        print(f"  Required: {needed_mb:,} MB (+20% margin) | Available: {free_mb:,} MB")
        print(f"  Please free up at least {needed_mb - free_mb:,} MB or specify another drive.")
        print(f"  Installation CANNOT proceed until space is available.\n")
        return

    # Final confirmation
    print("\n" + "=" * 70)
    print("  CONFIRMATION REQUIRED")
    print("=" * 70)
    confirm_msg = f"""
  The following actions will be performed upon your confirmation:
    - Download installers from official sources (if local packages unavailable)
    - Verify downloaded files with SHA-256 checksums
    - Create directories under: {plan['base_dir']}
    - Modify environment variables (listed above)
    - Run installation commands (may require admin/UAC elevation)
    - Reopen terminal to apply PATH changes

  Type 'confirm' to proceed, or 'cancel' to abort.
"""
    print(confirm_msg)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build pre-installation plan")
    parser.add_argument("envs", nargs="+", help="Environments to plan for")
    parser.add_argument("--base-dir", default=None, help="Base install directory")
    parser.add_argument("--existing", default=None, help="JSON file with existing env status")
    parser.add_argument("--version", action="append", metavar="ENV=VERSION",
                        help="Override version for an environment (e.g. --version Python=3.11.10)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Parse version overrides
    version_overrides = {}
    if args.version:
        for v in args.version:
            if "=" in v:
                env_name, ver = v.split("=", 1)
                version_overrides[env_name.strip()] = ver.strip()

    # Load existing status
    existing = {}
    if args.existing and os.path.isfile(args.existing):
        with open(args.existing, "r") as f:
            existing = json.load(f)

    base_dir = args.base_dir or os.path.join(get_system_drive(), "dev-tools")

    plan = build_plan(args.envs, base_dir, existing, version_overrides)

    if args.json:
        plan["dependency_order"] = DEPENDENCY_ORDER
        plan["resolve_order"] = resolve_dependencies(args.envs)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        print_plan(plan)


if __name__ == "__main__":
    main()
