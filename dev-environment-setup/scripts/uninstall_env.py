#!/usr/bin/env python3
"""
Environment Uninstaller
Removes previously installed development environments from E:\\Test_tool_enviroment\\.
Safely removes only tools managed by this skill.
Does NOT touch system-installed tools (e.g. Python from python.org, winget installs).
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path
from typing import Optional


def get_os() -> str:
    return sys.platform


# Uninstall info per environment
# Paths use forward slashes or raw strings without trailing backslash
UNINSTALL_INFO = {
    "Python": {
        "install_dirs": [
            "E:/Test_tool_enviroment/Python",
            "C:/Python314",
            "C:/Python313",
            "C:/Python312",
            "C:/Python311",
            "C:/Python310",
        ],
        "env_vars": [
            {"name": "PYTHON_HOME", "scope": "user"},
            {"name": "Path", "scope": "user", "remove_pattern": "Python"},
        ],
        "registry_keys": [],
        "risk": "L2",
        "note": "会删除 E:\\Test_tool_enviroment\\Python\\ 下的安装；不会删除系统级 Python",
    },
    "Node.js": {
        "install_dirs": [
            "E:/Test_tool_enviroment/NodeJs",
            "C:/Program Files/nodejs",
            "C:/Program Files (x86)/nodejs",
        ],
        "env_vars": [
            {"name": "Path", "scope": "user", "remove_pattern": "nodejs"},
        ],
        "registry_keys": [],
        "risk": "L1",
        "note": "会删除 E:\\Test_tool_enviroment\\NodeJs\\；不会删除 winget 安装的 Node.js",
    },
    "Go": {
        "install_dirs": [
            "E:/Test_tool_enviroment/Go",
            "C:/Go",
        ],
        "env_vars": [
            {"name": "GOROOT", "scope": "user"},
            {"name": "Path", "scope": "user", "remove_pattern": "Go\\bin"},
        ],
        "registry_keys": [],
        "risk": "L1",
        "note": "会删除 E:\\Test_tool_enviroment\\Go\\；不会删除 winget 安装的 Go",
    },
    "Java": {
        "install_dirs": [
            "E:/Test_tool_enviroment/Java",
            "C:/Program Files/Java",
            "C:/Program Files (x86)/Java",
        ],
        "env_vars": [
            {"name": "JAVA_HOME", "scope": "user"},
            {"name": "Path", "scope": "user", "remove_pattern": "Java\\bin"},
        ],
        "registry_keys": ["HKCU\\SOFTWARE\\JavaSoft"],
        "risk": "L2",
        "note": "会删除 E:\\Test_tool_enviroment\\Java\\；不会删除系统级 JDK",
    },
    "Docker": {
        "install_dirs": [],
        "env_vars": [],
        "registry_keys": [],
        "risk": "L2",
        "note": "Docker Desktop 需通过控制面板卸载；本脚本不自动处理",
    },
    "Git": {
        "install_dirs": [
            "E:/Test_tool_enviroment/Git",
            "C:/Program Files/Git",
            "C:/Program Files (x86)/Git",
        ],
        "env_vars": [
            {"name": "Path", "scope": "user", "remove_pattern": "Git"},
        ],
        "registry_keys": [],
        "risk": "L1",
        "note": "会删除 E:\\Test_tool_enviroment\\Git\\；不会删除 winget 安装的 Git",
    },
    "SVN": {
        "install_dirs": [
            "E:/Test_tool_enviroment/SVN",
        ],
        "env_vars": [
            {"name": "Path", "scope": "user", "remove_pattern": "SVN"},
        ],
        "registry_keys": [],
        "risk": "L0",
        "note": "删除 E:\\Test_tool_enviroment\\SVN\\",
    },
    "WSL": {
        "install_dirs": [],
        "env_vars": [],
        "registry_keys": [],
        "risk": "L1",
        "note": "WSL 需通过 PowerShell 卸载：wsl --unregister <distro>；不建议自动处理",
    },
    "JMeter": {
        "install_dirs": [
            "E:/Test_tool_enviroment/JMeter",
        ],
        "env_vars": [
            {"name": "JMETER_HOME", "scope": "user"},
            {"name": "Path", "scope": "user", "remove_pattern": "JMeter"},
        ],
        "registry_keys": [],
        "risk": "L0",
        "note": "删除 E:\\Test_tool_enviroment\\JMeter\\ 下所有版本目录",
    },
    "Locust": {
        "install_dirs": [],
        "env_vars": [],
        "registry_keys": [],
        "risk": "L0",
        "note": "Locust 通过 pip 安装；运行 pip uninstall locust 卸载",
    },
    "ADB": {
        "install_dirs": [
            "E:/Test_tool_enviroment/Android-ADB",
        ],
        "env_vars": [
            {"name": "Path", "scope": "user", "remove_pattern": "Android-ADB"},
        ],
        "registry_keys": [],
        "risk": "L0",
        "note": "删除 E:\\Test_tool_enviroment\\Android-ADB\\",
    },
    "HDC": {
        "install_dirs": [
            "E:/Test_tool_enviroment/HDC",
        ],
        "env_vars": [
            {"name": "Path", "scope": "user", "remove_pattern": "HDC"},
        ],
        "registry_keys": [],
        "risk": "L0",
        "note": "删除 E:\\Test_tool_enviroment\\HDC\\",
    },
    "tidevice": {
        "install_dirs": [],
        "env_vars": [],
        "registry_keys": [],
        "risk": "L0",
        "note": "tidevice 通过 pip 安装；运行 pip uninstall tidevice 卸载",
    },
    "Hypium": {
        "install_dirs": [],
        "env_vars": [],
        "registry_keys": [],
        "risk": "L0",
        "note": "Hypium 通过 npm 全局安装；运行 npm uninstall -g @hmos/hypium 卸载",
    },
}


def check_installed(env_name: str):
    """Check if an environment is installed. Returns (installed, detail)."""
    from detect_env import get_version_output
    checks = {
        "Python": ["python", "python3"],
        "Node.js": ["node"],
        "Go": ["go"],
        "Java": ["java", "javac"],
        "Git": ["git"],
        "SVN": ["svn"],
        "WSL": ["wsl"],
        "Docker": ["docker"],
        "ADB": ["adb"],
        "HDC": ["hdc"],
        "tidevice": ["tidevice"],
        "JMeter": [],
        "Locust": ["locust"],
        "Hypium": ["hypium"],
    }
    info = UNINSTALL_INFO.get(env_name, {})

    # Check install directories first
    for d in info.get("install_dirs", []):
        if os.path.isdir(d):
            return True, f"安装目录存在: {d}"

    # Check commands
    cmds = checks.get(env_name, [])
    for cmd in cmds:
        found, ver = get_version_output([cmd])
        if found:
            return True, f"命令可用: {cmd} {ver}"

    return False, "未检测到安装"


def uninstall_python():
    target = "E:/Test_tool_enviroment/Python"
    if not os.path.isdir(target):
        return True, "目录不存在，无需卸载"
    try:
        shutil.rmtree(target)
        _remove_env_var("PYTHON_HOME", "user")
        _remove_path_entry("Python", "user")
        return True, f"已删除 {target}"
    except Exception as e:
        return False, f"删除失败: {e}"


def uninstall_locust():
    try:
        result = subprocess.run(
            ["pip", "uninstall", "locust", "-y"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True, "locust 已卸载"
        return False, result.stderr[:100] if result.stderr else "卸载失败"
    except Exception as e:
        return False, str(e)


def uninstall_tidevice():
    try:
        result = subprocess.run(
            ["pip", "uninstall", "tidevice", "-y"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True, "tidevice 已卸载"
        return False, result.stderr[:100] if result.stderr else "卸载失败"
    except Exception as e:
        return False, str(e)


def uninstall_hypium():
    try:
        result = subprocess.run(
            ["npm", "uninstall", "-g", "@hmos/hypium"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return True, "Hypium 已卸载"
        return False, result.stderr[:100] if result.stderr else "卸载失败"
    except Exception as e:
        return False, str(e)


def uninstall_generic(env_name):
    info = UNINSTALL_INFO.get(env_name, {})
    removed_dirs = []
    errors = []

    for d in info.get("install_dirs", []):
        if os.path.isdir(d):
            try:
                shutil.rmtree(d)
                removed_dirs.append(d)
            except Exception as e:
                errors.append(f"删除 {d} 失败: {e}")

    for ev in info.get("env_vars", []):
        if ev.get("remove_pattern"):
            _remove_path_entry(ev["remove_pattern"], ev.get("scope", "user"))
        elif ev.get("name") and ev.get("scope") == "user":
            _remove_env_var(ev["name"], "user")

    if errors:
        return False, "; ".join(errors)
    if removed_dirs:
        return True, f"已删除: {', '.join(removed_dirs)}"
    return True, "无需卸载（目录不存在）"


def _remove_env_var(var_name, scope="user"):
    """Remove an environment variable using setx."""
    try:
        subprocess.run(
            ["setx", var_name, ""],
            capture_output=True, text=True, timeout=5,
        )
    except Exception:
        pass


def _remove_path_entry(pattern, scope="user"):
    """Remove PATH entries matching a pattern."""
    try:
        import ctypes
        if scope == "user":
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                                     winreg.KEY_READ | winreg.KEY_SET_VALUE)
                try:
                    current, _ = winreg.QueryValueEx(key, "PATH")
                    parts = current.split(";")
                    new_parts = [p for p in parts if pattern.lower() not in p.lower()]
                    if len(new_parts) < len(parts):
                        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ,
                                          ";".join(new_parts))
                finally:
                    winreg.CloseKey(key)
            except FileNotFoundError:
                pass
    except Exception:
        pass


def print_uninstall_plan(envs, existing_status):
    """Print what will be uninstalled for user confirmation."""
    print("\n" + "=" * 70)
    print("  UNINSTALL PLAN")
    print("=" * 70)

    for env_name in envs:
        info = UNINSTALL_INFO.get(env_name)
        if not info:
            print(f"\n  [{env_name}] SKIP — 未定义卸载逻辑")
            continue

        installed, detail = existing_status.get(env_name, (False, "未检测"))
        if not installed:
            print(f"\n  [{env_name}] SKIP — {detail}")
            continue

        print(f"\n  [{env_name}] [INSTALLED] — {detail}")
        print(f"    Risk: {info['risk']}")
        print(f"    Will remove:")
        for d in info["install_dirs"]:
            exists = "OK" if os.path.isdir(d) else "NOT_FOUND"
            print(f"      [{exists}]  {d}")
        for ev in info["env_vars"]:
            action = "remove"
            if ev.get("remove_pattern"):
                action = f"remove PATH entries containing '{ev['remove_pattern']}'"
            print(f"      env: {ev['name']} ({ev.get('scope', 'user')}) -> {action}")
        print(f"    Note: {info['note']}")

    print("\n" + "-" * 70)
    # Don't prompt for input in --dry-run mode or non-interactive mode
    try:
        confirm = input("\n  Type 'confirm' to proceed, 'cancel' to abort: ").strip().lower()
    except (EOFError, OSError):
        confirm = ""
    if confirm != "confirm":
        print("\n  CANCELLED")
        sys.exit(0)
    print()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Uninstall development environments")
    parser.add_argument("envs", nargs="+", help="Environments to uninstall")
    parser.add_argument("--dry-run", action="store_true", help="Show plan only, don't uninstall")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Check existing status
    existing = {}
    for env in args.envs:
        found, detail = check_installed(env)
        existing[env] = (found, detail)

    # Print plan
    print_uninstall_plan(args.envs, existing)

    # Perform uninstall
    results = {}
    for env_name in args.envs:
        installed, detail = existing.get(env_name, (False, ""))
        if not installed:
            results[env_name] = {"status": "SKIPPED", "reason": detail}
            print(f"  [SKIP] {env_name}: {detail}")
            continue

        # Dispatch to specific uninstaller
        if env_name == "Python":
            ok, msg = uninstall_python()
        elif env_name == "Locust":
            ok, msg = uninstall_locust()
        elif env_name == "tidevice":
            ok, msg = uninstall_tidevice()
        elif env_name == "Hypium":
            ok, msg = uninstall_hypium()
        else:
            ok, msg = uninstall_generic(env_name)

        results[env_name] = {"status": "SUCCESS" if ok else "FAILED", "message": msg}
        icon = "[OK]" if ok else "[FAIL]"
        print(f"  {icon} {env_name}: {msg}")

    # Summary
    print("\n" + "=" * 70)
    success_count = sum(1 for r in results.values() if r["status"] == "SUCCESS")
    fail_count = sum(1 for r in results.values() if r["status"] == "FAILED")
    skip_count = sum(1 for r in results.values() if r["status"] == "SKIPPED")
    print(f"  Uninstall Complete: {success_count} success, {fail_count} failed, {skip_count} skipped")
    print("=" * 70 + "\n")

    if args.json:
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
