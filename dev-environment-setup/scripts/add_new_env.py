#!/usr/bin/env python3
"""
Add New Environment Wizard
Interactive wizard to add a new environment to the dev-environment-setup catalog.
Guides user through: name, description, commands, mirrors, versions, dependencies.
Outputs a ready-to-use entry for env_catalog.md and the required code updates.
"""

import os
import sys
from pathlib import Path


CATALOG_FILE = Path(__file__).parent.parent / "references" / "env_catalog.md"
DETECT_FILE = Path(__file__).parent / "detect_env.py"
INSTALLER_FILE = Path(__file__).parent / "installer.py"
BUILD_PLAN_FILE = Path(__file__).parent / "build_plan.py"


def ask(prompt: str, default: str = "") -> str:
    """Ask user a question with optional default."""
    suffix = f" [{default}]" if default else ""
    try:
        answer = input(f"  {prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default if default else ""
    return answer or default


def main():
    print("\n" + "=" * 60)
    print("  Add New Environment Wizard")
    print("=" * 60)
    print("""
  This wizard will help you add a new environment to the catalog.
  It will generate:
    1. An entry for references/env_catalog.md
    2. Code additions for scripts/detect_env.py
    3. Mirror configuration for scripts/installer.py
    4. Build plan entries for scripts/build_plan.py

  Press Ctrl+C at any time to cancel.
""")

    # Step 1: Basic info
    print("\n--- Step 1: Basic Information ---")
    name = ask("Environment name (e.g. Rust, Cargo)", "MyTool")
    if not name:
        print("  Cancelled.")
        return

    description = ask("Description", f"{name} development tool")
    category = ask("Category", "tool")
    print("  Categories: backend, fullstack, infra, tool, mobile, performance")

    # Step 2: Commands
    print("\n--- Step 2: Verification Commands ---")
    cmds_str = ask("Version check commands (space-separated, e.g. 'rustc --version')", f"{name.lower()} --version")
    commands = [c.strip() for c in cmds_str.split() if c.strip()]

    # Step 3: Versions
    print("\n--- Step 3: Available Versions ---")
    versions_str = ask("Available versions (comma-separated, newest first, or 'latest' only)", "latest")
    if versions_str.strip().lower() == "latest":
        versions = []
    else:
        versions = [v.strip() for v in versions_str.split(",") if v.strip()]

    # Step 4: Download
    print("\n--- Step 4: Download Sources ---")
    primary_mirror = ask("Primary mirror URL (trailing slash)", "")
    backup1 = ask("Backup mirror 1 URL (trailing slash)", "")
    backup2 = ask("Backup mirror 2 URL (official source)", "")
    url_pattern = ask("URL pattern (use {mirror} and {version} as placeholders)", "")

    # Step 5: Installation
    print("\n--- Step 5: Installation ---")
    install_method = ask("Install method", "download")
    print("  Methods: download, pip, npm, winget, brew, apt, manual")
    install_cmd = ask("Install command (use {filepath} for downloaded file)", "")
    install_dir = ask("Install directory template (use {base_dir} and {version})",
                      f"E:/Test_tool_enviroment/{name}/")

    # Step 6: Dependencies
    print("\n--- Step 6: Dependencies ---")
    deps_str = ask("Required dependencies (comma-separated names, or empty)", "")
    dependencies = []
    if deps_str.strip():
        for dep in deps_str.split(","):
            dep = dep.strip()
            req = ask(f"  Is '{dep}' required for install? (y/n)", "y")
            dependencies.append((dep, req.lower() == "y"))

    # Step 7: Environment variables
    print("\n--- Step 7: Environment Variables ---")
    env_vars_str = ask("Env vars to set (format: NAME=scope:value, comma-separated, or empty)", "")
    env_vars = []
    if env_vars_str.strip():
        for ev in env_vars_str.split(","):
            ev = ev.strip()
            if "=" in ev:
                var_name, scope_value = ev.split("=", 1)
                if ":" in scope_value:
                    scope, value = scope_value.split(":", 1)
                else:
                    scope, value = "user", scope_value
                env_vars.append({"name": var_name.strip(), "scope": scope.strip(), "value": value.strip()})

    # Step 8: Risk
    print("\n--- Step 8: Risk Assessment ---")
    risk = ask("Risk level", "L1")
    print("  Levels: L0 (read-only), L1 (install only), L2 (driver/registry changes)")

    # Step 9: OS support
    print("\n--- Step 9: OS Support ---")
    os_support = ask("Supported OS (win32,darwin,linux — comma-separated)", "win32,darwin,linux")
    os_list = [o.strip() for o in os_support.split(",") if o.strip()]
    os_condition = ask("OS-specific notes (or empty)", "")

    # Step 10: Generate output
    print("\n" + "=" * 60)
    print("  Generated Catalog Entry")
    print("=" * 60)

    # Env catalog entry
    print(f"\n### {len([l for l in CATALOG_FILE.read_text(encoding='utf-8').splitlines() if l.startswith('### ')]) + 1}. {name}")
    print(f"\n| 字段 | 值 |")
    print(f"|------|---|")
    print(f"| **用途** | {description} |")
    if versions:
        print(f"| **可用版本（最近 5 个）** | {' / '.join(versions)} |")
    else:
        print(f"| **版本策略** | 安装最新版 |")
    print(f"| **官方来源** | `{url_pattern or 'N/A'}` |")
    print(f"| **本地包目录** | `{install_dir}` |")
    print(f"| **网络要求** | {'需外网访问 ' + primary_mirror if primary_mirror else '无本地包时需外网'} |")
    if env_vars:
        ev_str = "; ".join(f"{v['name']}({v['scope']})={v['value']}" for v in env_vars)
        print(f"| **环境变量** | {ev_str} |")
    print(f"| **验证命令** | `{'` , `'.join(commands) if commands else 'none'}` |")
    print(f"| **风险等级** | {risk} |")

    # detect_env.py entry
    print(f"\n--- detect_env.py addition ---")
    print(f'''    Runtime(
        "{name}",
        {repr(commands)},
        min_version=None,
        category="{category}",
        description="{description}",
        env_var="{env_vars[0]['name'] if env_vars else ''}",
        supported_os={repr(os_list)},
        {f'special_conditions={{"win32": "{os_condition}"}}' if os_condition else ''},
    ),''')

    # installer.py mirrors entry
    print(f"\n--- installer.py MIRROR_SOURCES addition ---")
    mirrors = [m for m in [primary_mirror, backup1, backup2] if m]
    if mirrors:
        print(f'''    "{name}": {{
        "primary":   {repr(mirrors[0])},
        "fallbacks": [{", ".join(repr(m) for m in mirrors[1:])}],
    }},''')

    # build_plan.py entries
    print(f"\n--- build_plan.py additions ---")
    print(f'''    "{name}": {{"supported": {repr(os_list)}, "condition": {repr(os_condition)} }},''')
    if env_vars:
        print(f'''    "{name}": {repr(env_vars)},''')
    print(f'''    "{name}": ["{name}"],''')  # network_domains
    print(f'''    "{name}": "{risk}",''')  # risk_level
    print(f'''    "{name}": 100,''')  # size_estimate
    if dependencies:
        dep_list = ", ".join(f'("{dep[0]}", {str(dep[1]).lower()})' for dep in dependencies)
        print(f'''    "{name}": [{dep_list}],''')  # dependencies

    print(f"\n{'=' * 60}")
    print("  Wizard complete.")
    print(f"  Log saved, but manual edits required for:")
    print(f"    - {CATALOG_FILE}")
    print(f"    - {DETECT_FILE}")
    print(f"    - {INSTALLER_FILE}")
    print(f"    - {BUILD_PLAN_FILE}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
