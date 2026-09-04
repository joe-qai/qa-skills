#!/usr/bin/env python3
"""
Dev Environment Detector
Scans the system for installed runtimes, their versions, paths, and PATH configuration.
Output: one item per line with clear status.
Also checks OS compatibility for each environment.
"""

import subprocess
import sys
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Runtime:
    name: str
    commands: list[str]
    min_version: Optional[str] = None
    category: str = "runtime"
    description: str = ""
    env_var: str = ""          # e.g. "PYTHON_HOME", "GOROOT"
    supported_os: list[str] = field(default_factory=lambda: ["win32", "darwin", "linux"])
    # special_conditions: dict of (os -> condition_description) for OS-specific notes
    special_conditions: dict = field(default_factory=dict)


RUNTIMES = [
    Runtime(
        "Python",
        ["python", "python3"],
        min_version="3.10.0",
        category="backend",
        description="后端运行时，支持 Django / FastAPI / 压测脚本",
        env_var="PYTHON_HOME",
    ),
    Runtime(
        "Node.js",
        ["node"],
        min_version="18.0.0",
        category="fullstack",
        description="前后端运行时，支持 npm/pnpm/yarn",
        env_var="PATH",
    ),
    Runtime(
        "Go",
        ["go"],
        min_version="1.21.0",
        category="backend",
        description="后端运行时，支持 Gin / Fiber",
        env_var="GOROOT",
    ),
    Runtime(
        "Java",
        ["java", "javac"],
        min_version="17.0.0",
        category="backend",
        description="后端运行时，支持 Spring Boot / JMeter 依赖",
        env_var="JAVA_HOME",
    ),
    Runtime(
        "Docker",
        ["docker", "docker-compose", "docker compose"],
        min_version=None,
        category="infra",
        description="容器化运行环境（Windows 需 WSL2）",
        env_var="PATH",
        special_conditions={
            "win32": "需要 WSL2（编号 8）",
            "linux": "需要 systemd 支持",
        },
    ),
    Runtime(
        "Git",
        ["git"],
        min_version=None,
        category="tool",
        description="版本控制",
        env_var="PATH",
    ),
    Runtime(
        "SVN",
        ["svn"],
        min_version=None,
        category="tool",
        description="版本控制（Subversion）",
        env_var="PATH",
    ),
    Runtime(
        "WSL",
        ["wsl"],
        min_version=None,
        category="infra",
        description="Windows 子系统 for Linux（Docker 前置依赖）",
        env_var="",
        supported_os=["win32"],
    ),
    Runtime(
        "ADB",
        ["adb"],
        min_version=None,
        category="mobile",
        description="Android 设备调试 / APP 自动化测试",
        env_var="PATH",
    ),
    Runtime(
        "HDC",
        ["hdc"],
        min_version=None,
        category="mobile",
        description="华为鸿蒙设备调试（HDC）",
        env_var="PATH",
    ),
    Runtime(
        "tidevice",
        ["tidevice"],
        min_version=None,
        category="mobile",
        description="iOS 设备调试（需 Python 3.8+，Windows 支持有限）",
        env_var="",
        supported_os=["win32", "darwin"],
        special_conditions={
            "win32": "部分功能受限，推荐 macOS",
            "darwin": "完全支持",
        },
    ),
    Runtime(
        "JMeter",
        ["jmeter"],
        min_version=None,
        category="performance",
        description="HTTP 性能/压力测试（需 Java）",
        env_var="JMETER_HOME",
    ),
    Runtime(
        "Locust",
        ["locust"],
        min_version=None,
        category="performance",
        description="Python 分布式负载测试（需 Python 3.8+）",
        env_var="",
    ),
    Runtime(
        "Hypium",
        ["hypium"],
        min_version=None,
        category="mobile",
        description="鸿蒙测试框架（@hmos/hypium，需 Node.js 18+）",
        env_var="",
        supported_os=["win32", "darwin"],
        special_conditions={"linux": "不支持"},
    ),
]

MOBILE_TOOLS = [
    {"name": "hypium", "cmd": ["hypium"], "deps": "node", "category": "mobile",
     "description": "鸿蒙测试框架（@hmos/hypium）", "env_var": ""},
    {"name": "node", "cmd": ["node"], "deps": None, "category": "fullstack",
     "description": "Node.js（Hypium 前置依赖）", "env_var": "PATH"},
]

PACKAGE_MANAGERS = [
    {"name": "pip", "cmd": ["pip"], "deps": "python"},
    {"name": "pip3", "cmd": ["pip3"], "deps": "python"},
    {"name": "npm", "cmd": ["npm"], "deps": "node"},
    {"name": "pnpm", "cmd": ["pnpm"], "deps": "node"},
    {"name": "yarn", "cmd": ["yarn"], "deps": "node"},
    {"name": "winget", "cmd": ["winget"], "deps": None},
    {"name": "brew", "cmd": ["brew"], "deps": None},
]


def get_os() -> str:
    return sys.platform


def get_os_name() -> str:
    """Return human-readable OS name."""
    mapping = {"win32": "Windows", "darwin": "macOS", "linux": "Linux"}
    return mapping.get(get_os(), get_os())


def check_os_compatibility(runtime: Runtime) -> tuple[bool, str]:
    """Check if current OS supports this runtime. Return (compatible, reason)."""
    current = get_os()
    if current in runtime.supported_os:
        condition = runtime.special_conditions.get(current)
        if condition:
            return True, condition  # compatible but with note
        return True, ""
    # Check if OS is explicitly not supported
    all_os = ["win32", "darwin", "linux"]
    if runtime.supported_os == all_os:
        return True, ""
    unsupported = [mapping.get(o, o) for o in all_os if o not in runtime.supported_os]
    return False, f"不支持 {', '.join(unsupported)}"


def get_system_drives() -> list[str]:
    drives = []
    for i in range(65, 91):
        letter = f"{chr(i)}:\\"
        if os.path.exists(letter):
            drives.append(letter)
    return drives


def find_command_path(cmd: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["where", cmd] if get_os() == "win32" else ["which", cmd],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            paths = [p.strip() for p in result.stdout.strip().split("\n") if p.strip()]
            return paths[0] if paths else None
    except Exception:
        pass
    return None


def get_version_output(commands: list[str]) -> tuple[bool, str]:
    for cmd in commands:
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                env=os.environ.copy(),
                shell=(get_os() == "win32"),
            )
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
                if lines:
                    return True, lines[0]
        except Exception:
            continue
    return False, ""


def main():
    os_name = get_os()
    os_readable = get_os_name()
    drives = get_system_drives()
    system_drive = drives[0] if drives else "C:\\"

    print("=" * 60)
    print("  Dev Environment Detection")
    print("=" * 60)
    print(f"\n  OS: {os_readable} ({os_name})")
    print(f"  Drives: {', '.join(drives)}")
    print(f"  System Drive: {system_drive}\n")

    # ---- Section 1: Runtimes (one per line) ----
    print("-" * 60)
    print("  Runtime & Tool Status")
    print("-" * 60)
    print()

    runtime_status = {}
    for idx, runtime in enumerate(RUNTIMES, 1):
        compatible, condition = check_os_compatibility(runtime)
        found, version_str = get_version_output(runtime.commands)
        path = find_command_path(runtime.commands[0]) if found else ""
        status = "[OK]" if found else ("[SKIP]" if not compatible else "[MISS]")

        runtime_status[runtime.name] = {
            "found": found,
            "version": version_str,
            "path": path,
            "category": runtime.category,
            "description": runtime.description,
            "commands": runtime.commands,
            "env_var": runtime.env_var,
            "compatible": compatible,
            "condition": condition,
        }

        # Build display line
        if found:
            ver_display = version_str[:27] + "..." if len(version_str) > 30 else version_str
            path_display = f"  -> {path}" if path else ""
            cond_note = f"  [{condition}]" if condition else ""
            print(f"  [{idx}] {runtime.name:<12} {status}  {ver_display}{path_display}")
            print(f"         {runtime.description}{cond_note}")
        elif not compatible:
            print(f"  [{idx}] {runtime.name:<12} [SKIP]  {runtime.description}")
            print(f"         OS 不兼容: {condition}")
        else:
            print(f"  [{idx}] {runtime.name:<12} {status}  {runtime.description}")
        print()

    # ---- Section 2: Package managers ----
    print("-" * 60)
    print("  Package Manager Status")
    print("-" * 60)
    print()

    pkg_status = {}
    for idx, pkg in enumerate(PACKAGE_MANAGERS, 1):
        found, version_str = get_version_output(pkg["cmd"])
        status = "[OK]" if found else "[MISS]"
        pkg_status[pkg["name"]] = {"found": found, "version": version_str, "deps": pkg["deps"]}
        ver_display = version_str if version_str else "—"
        print(f"  [{idx}] {pkg['name']:<12} {status}  {ver_display}")
    print()

    # ---- Section 3: Summary ----
    installed_runtimes = [name for name, s in runtime_status.items() if s["found"]]
    missing_runtimes = [name for name, s in runtime_status.items() if not s["found"] and s["compatible"]]
    incompatible_runtimes = [name for name, s in runtime_status.items() if not s["compatible"]]

    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"\n  Installed runtimes: {len(installed_runtimes)} / {len(RUNTIMES)}")
    if installed_runtimes:
        for name in installed_runtimes:
            s = runtime_status[name]
            ver = s["version"].split()[0] if s["version"] else ""
            print(f"    [OK] {name}  {ver}")
    if missing_runtimes:
        print(f"\n  Missing runtimes:   {len(missing_runtimes)} / {len(RUNTIMES)}")
        for name in missing_runtimes:
            s = runtime_status[name]
            print(f"    [MISS] {name}  —  {s['description']}")
    if incompatible_runtimes:
        print(f"\n  OS Incompatible:    {len(incompatible_runtimes)}")
        for name in incompatible_runtimes:
            s = runtime_status[name]
            print(f"    [SKIP] {name}  —  {s['condition']}")

    print(f"\n  Install base path: {system_drive}")
    print(f"\n  Next step: Select missing environments to install\n")


if __name__ == "__main__":
    main()
