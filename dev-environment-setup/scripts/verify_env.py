#!/usr/bin/env python3
"""
Environment Verifier
Checks each installed environment and reports PASS / FAIL / MISSING.
Designed for post-installation verification; each environment is checked independently.
One failure does not block verification of other environments.
"""

import subprocess
import sys
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CheckResult:
    name: str
    status: str          # "PASS" / "FAIL" / "MISSING" / "BLOCKED"
    version: str = ""
    path: str = ""
    details: str = ""
    action: str = ""     # what was done (installed / skipped / failed)


# Verification checks per environment
VERIFICATION_CHECKS = {
    "Python": {
        "commands": [["python", "--version"], ["python3", "--version"], ["pip", "--version"]],
        "key_files": [],
        "env_vars": ["PYTHON_HOME"],
        "description": "Python 运行时",
    },
    "Node.js": {
        "commands": [["node", "--version"], ["npm", "--version"]],
        "key_files": [],
        "env_vars": [],
        "description": "Node.js 运行时",
    },
    "Go": {
        "commands": [["go", "version"]],
        "key_files": [],
        "env_vars": ["GOROOT"],
        "description": "Go 编译器",
    },
    "Java": {
        "commands": [["java", "-version"], ["javac", "-version"]],
        "key_files": [],
        "env_vars": ["JAVA_HOME"],
        "description": "Java JDK",
    },
    "Docker": {
        "commands": [["docker", "--version"], ["docker", "compose", "version"]],
        "key_files": [],
        "env_vars": [],
        "description": "Docker 容器引擎",
    },
    "Git": {
        "commands": [["git", "--version"]],
        "key_files": [],
        "env_vars": [],
        "description": "Git 版本控制",
    },
    "SVN": {
        "commands": [["svn", "--version"]],
        "key_files": [],
        "env_vars": [],
        "description": "SVN 版本控制",
    },
    "WSL": {
        "commands": [["wsl", "--version"], ["wsl", "-l", "-v"]],
        "key_files": [],
        "env_vars": [],
        "description": "WSL Linux 子系统",
    },
    "JMeter": {
        "commands": [],  # checked via bat file or dir existence
        "key_files": ["bin/jmeter.bat", "bin/jmeter.sh"],
        "env_vars": ["JMETER_HOME"],
        "description": "JMeter 性能测试工具",
    },
    "Locust": {
        "commands": [["locust", "--version"]],
        "key_files": [],
        "env_vars": [],
        "description": "Locust 负载测试工具",
    },
    "ADB": {
        "commands": [["adb", "--version"]],
        "key_files": ["adb.exe", "fastboot.exe"],
        "env_vars": [],
        "description": "Android ADB 调试工具",
    },
    "HDC": {
        "commands": [["hdc", "-v"], ["hdc", "w"]],
        "key_files": ["hdc.exe"],
        "env_vars": [],
        "description": "华为 HDC 鸿蒙调试工具",
    },
    "tidevice": {
        "commands": [["tidevice", "--version"]],
        "key_files": [],
        "env_vars": [],
        "description": "tidevice iOS 调试工具",
    },
    "Hypium": {
        "commands": [["hypium", "--version"]],
        "key_files": [],
        "env_vars": [],
        "description": "Hypium 鸿蒙测试框架",
    },
}


def run_cmd(cmd: list[str], timeout: int = 10) -> tuple[bool, str]:
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=_get_full_env(),
            shell=(sys.platform == "win32"),
        )
        if result.returncode == 0:
            output = (result.stdout or result.stderr or "").strip()
            # Extract version from output
            lines = [l.strip() for l in output.split("\n") if l.strip()]
            version = lines[0] if lines else output[:60]
            return True, version
    except Exception:
        pass
    return False, ""


def _get_full_env() -> dict:
    env = os.environ.copy()
    common_paths = [
        r"E:\Test_tool_enviroment\Python\Scripts",
        r"E:\Test_tool_enviroment\NodeJs",
        r"E:\Test_tool_enviroment\Go\bin",
        r"E:\Test_tool_enviroment\Java\bin",
        r"E:\Test_tool_enviroment\JMeter\*\bin",
        r"E:\Test_tool_enviroment\Android-ADB\platform-tools",
        r"C:\Program Files\Git\cmd",
        r"C:\Program Files\Docker\Docker\resources\bin",
        r"C:\Windows\System32",
    ]
    existing = env.get("PATH", "")
    for p in common_paths:
        if p not in existing:
            env["PATH"] = p + ";" + existing
    return env


def check_env(env_name: str) -> CheckResult:
    """Verify a single environment. Returns CheckResult independently."""
    checks = VERIFICATION_CHECKS.get(env_name)
    if not checks:
        return CheckResult(env_name, "MISSING", details=f"未定义验证规则")

    version = ""
    path = ""
    passed_any = False

    # Try command checks
    for cmd in checks["commands"]:
        ok, out = run_cmd(cmd)
        if ok:
            passed_any = True
            version = out
            # Extract path from output if possible
            if " -> " in out:
                path = out.split(" -> ")[-1].strip()
            break

    # Try key file checks (for tools without --version)
    if not passed_any:
        base_dir = os.path.join("E:\\Test_tool_enviroment", env_name)
        install_dirs = [
            base_dir,
            os.path.join("E:\\Test_tool_enviroment", env_name, "latest"),
        ]
        # Special cases for versioned directories
        if env_name == "JMeter":
            for v in ["5.6.2", "5.6.1", "5.5.1", "5.4.3"]:
                install_dirs.append(os.path.join("E:\\Test_tool_enviroment", "JMeter", v))
        if env_name == "Android-ADB":
            install_dirs = [os.path.join("E:\\Test_tool_enviroment", "Android-ADB", "platform-tools")]

        for d in install_dirs:
            if os.path.isdir(d):
                for kf in checks["key_files"]:
                    full = os.path.join(d, kf)
                    if os.path.isfile(full):
                        passed_any = True
                        path = d
                        version = f"installed @ {d}"
                        break
            if passed_any:
                break

    # Check env vars
    env_status = []
    for var in checks["env_vars"]:
        val = os.environ.get(var, "")
        if val:
            env_status.append(f"{var}={val[:50]}")
        else:
            env_status.append(f"{var}=NOT_SET")

    # Determine final status
    if passed_any:
        status = "PASS"
        detail = f"version={version}"
        if path:
            detail += f"  path={path}"
    else:
        status = "FAIL"
        detail = f"command not found; env: {'; '.join(env_status)}"

    return CheckResult(
        name=env_name,
        status=status,
        version=version,
        path=path,
        details=detail,
        action="verified" if status == "PASS" else "needs_install",
    )


def verify_selected(envs: list[str]) -> list[CheckResult]:
    """Verify multiple environments independently. One failure doesn't block others."""
    results = []
    for env_name in envs:
        try:
            result = check_env(env_name)
            results.append(result)
        except Exception as e:
            results.append(CheckResult(env_name, "FAIL", details=f"verification error: {e}"))
    return results


def print_results(results: list[CheckResult]):
    """Print verification results in a clean table."""
    print("\n" + "=" * 70)
    print("  ENVIRONMENT VERIFICATION REPORT")
    print("=" * 70)

    # Group by status
    pass_items = [r for r in results if r.status == "PASS"]
    fail_items = [r for r in results if r.status == "FAIL"]
    missing_items = [r for r in results if r.status == "MISSING"]

    print(f"\n  Total checked: {len(results)}")
    print(f"  PASS:          {len(pass_items)}")
    print(f"  FAIL:          {len(fail_items)}")
    print(f"  MISSING:       {len(missing_items)}")

    if pass_items:
        print("\n" + "-" * 70)
        print("  PASSED")
        print("-" * 70)
        for r in pass_items:
            ver_display = r.version[:35] + "..." if len(r.version) > 35 else r.version
            print(f"    [PASS] {r.name:<15} {ver_display}")
            if r.path:
                print(f"             path: {r.path}")

    if fail_items:
        print("\n" + "-" * 70)
        print("  FAILED")
        print("-" * 70)
        for r in fail_items:
            print(f"    [FAIL] {r.name:<15} {r.details}")

    if missing_items:
        print("\n" + "-" * 70)
        print("  MISSING (no verification rules)")
        print("-" * 70)
        for r in missing_items:
            print(f"    [MISS] {r.name}")

    print("\n" + "=" * 70)

    # Summary
    all_pass = all(r.status == "PASS" for r in results) and len(fail_items) == 0 and len(missing_items) == 0
    if all_pass:
        print("  Status: ALL CHECKS PASSED")
    elif fail_items:
        print(f"  Status: {len(fail_items)} CHECK(S) FAILED — review needed")
    else:
        print("  Status: SOME ENVIRONMENTS NEED INSTALLATION")
    print("=" * 70 + "\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Verify installed development environments")
    parser.add_argument("envs", nargs="+", help="Environments to verify (e.g. Python Go JMeter)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    results = verify_selected(args.envs)

    if args.json:
        import json
        data = {
            "results": [
                {
                    "name": r.name,
                    "status": r.status,
                    "version": r.version,
                    "path": r.path,
                    "details": r.details,
                    "action": r.action,
                }
                for r in results
            ],
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r.status == "PASS"),
                "failed": sum(1 for r in results if r.status == "FAIL"),
                "missing": sum(1 for r in results if r.status == "MISSING"),
            },
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_results(results)


if __name__ == "__main__":
    main()
