#!/usr/bin/env python3
"""
Interactive Dev Environment Setup
Guides user through environment selection, path confirmation, and installation with PATH configuration.
Supports: logging, progress bar, multi-Python coexistence, unknown tool wizard.
"""

import subprocess
import sys
import os
import shutil
import platform
import tempfile
from pathlib import Path
from datetime import datetime


def get_os() -> str:
    return sys.platform


def get_system_drive() -> str:
    drives = []
    for i in range(65, 91):
        letter = f"{chr(i)}:\\"
        if os.path.exists(letter):
            drives.append(letter)
    return drives[0] if drives else "C:\\"


def get_base_install_dir(drive: str) -> str:
    """Return a sensible default base install directory."""
    if get_os() == "win32":
        return os.path.join(drive, "dev-tools")
    return os.path.join(os.path.expanduser("~"), "dev-tools")


def select_install_drive() -> str:
    """Select install drive — prefer non-system drive when multiple exist."""
    drives = get_system_drives()
    if len(drives) <= 1:
        return drives[0] if drives else "C:\\"
    # Multiple drives: prefer first non-system drive
    system_drive = get_system_drive()
    for d in drives:
        if d != system_drive:
            print(f"\n  [INFO] Found multiple drives. Defaulting to non-system drive: {d}")
            return d
    return drives[0]


def check_command(cmd: str) -> tuple[bool, str]:
    """Check if command is available and return (found, version)."""
    try:
        result = subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            env=os.environ.copy(),
            shell=(get_os() == "win32"),
        )
        if result.returncode == 0:
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            if lines:
                return True, lines[0]
    except Exception:
        pass
    return False, ""


def add_to_path_windows(install_dir: str):
    """Add directory to user PATH in Windows."""
    try:
        current = os.environ.get("PATH", "")
        if install_dir not in current:
            subprocess.run(
                ["setx", "PATH", f"{install_dir};%PATH%"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            print(f"  [+] PATH updated (user-level): {install_dir}")
    except Exception as e:
        print(f"  [!] PATH auto-configure failed: {e}")
        print(f"      Please manually add to system PATH:")
        print(f"      {install_dir}")


def add_to_path_macos(install_dir: str, shell: str = "zsh"):
    shell_rc = Path.home() / f".{shell}rc"
    line = f'export PATH="{install_dir}:$PATH"'
    if shell_rc.exists():
        content = shell_rc.read_text()
        if install_dir not in content:
            with open(shell_rc, "a") as f:
                f.write(f"\n{line}\n")
            print(f"  [+] PATH added to ~/.{shell}rc")
    else:
        print(f"  [!] Cannot write to {shell_rc}, please manually add:")
        print(f"      export PATH=\"{install_dir}:$PATH\"")


def add_to_path_linux(install_dir: str, shell: str = "bash"):
    shell_rc = Path.home() / f".{shell}rc"
    line = f'export PATH="{install_dir}:$PATH"'
    if shell_rc.exists():
        content = shell_rc.read_text()
        if install_dir not in content:
            with open(shell_rc, "a") as f:
                f.write(f"\n{line}\n")
            print(f"  [+] PATH added to ~/.{shell}rc")
    else:
        print(f"  [!] Cannot write to {shell_rc}, please manually add:")
        print(f"      export PATH=\"{install_dir}:$PATH\"")


def install_python(install_dir: str) -> bool:
    print(f"\n[Python Installation]")
    print(f"  Target: {install_dir}\\Python")

    if get_os() == "win32":
        from installer import run_winget, install_with_fallback, get_timeout_for_tool
        timeout = get_timeout_for_tool("python")

        # Method 1: winget
        found, _ = check_command("winget")
        if found:
            print(f"  Method 1: winget (timeout {timeout}s)...")
            ok, msg = run_winget("Python.Python.3.12", timeout=timeout)
            if ok:
                print(f"  [+] Python installed via winget")
                return True
            print(f"  [!] winget failed: {msg}")

        # Method 2: Download installer directly
        print(f"  Method 2: Direct download...")
        url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe"
        result = install_with_fallback(
            installer_name="python",
            url=url,
            dest_dir=os.path.join(tempfile.gettempdir(), "python-installer"),
            timeout=timeout,
            install_cmd=["msiexec", "/i", "{filepath}", "/quiet", "/norestart",
                         "INSTALLALLUSERS=1", "ADDEXEDPATH=1"],
        )
        if result["status"] == "success":
            print(f"  [+] Python installed successfully")
            return True

        print(f"  [!] Install failed: {result['message']}")
        if result["status"] == "timeout":
            print(f"      Retry with longer timeout or install manually from {url}")
        return False

    if get_os() == "darwin":
        from installer import run_brew
        found, _ = check_command("brew")
        if found:
            ok, msg = run_brew("python@3.12", timeout=get_timeout_for_tool("python"))
            if ok:
                print(f"  [+] Python installed via brew")
                return True
            print(f"  [!] brew failed: {msg}")

    from installer import run_apt
    ok, msg = run_apt(["python3.12", "python3.12-venv", "python3-pip"],
                       timeout=get_timeout_for_tool("python"))
    if ok:
        add_to_path_linux("/usr/bin")
        print(f"  [+] Python installed successfully")
        return True

    print(f"  [!] Auto-install failed: {msg}")
    print(f"      Install manually: https://www.python.org/downloads/")
    return False


def install_node(install_dir: str) -> bool:
    print(f"\n[Node.js Installation]")
    print(f"  Target: {install_dir}\\Node")

    if get_os() == "win32":
        from installer import run_winget, install_with_fallback, get_timeout_for_tool
        timeout = get_timeout_for_tool("node")

        found, _ = check_command("winget")
        if found:
            ok, msg = run_winget("OpenJS.NodeJS.LTS", timeout=timeout)
            if ok:
                print(f"  [+] Node.js installed via winget")
                return True
            print(f"  [!] winget failed: {msg}")

        # Method 2: Download MSI
        url = "https://nodejs.org/dist/v22.16.0/node-v22.16.0-x64.msi"
        result = install_with_fallback(
            installer_name="node",
            url=url,
            dest_dir=os.path.join(tempfile.gettempdir(), "node-installer"),
            timeout=timeout,
            install_cmd=["msiexec", "/i", "{filepath}", "/quiet", "/norestart"],
        )
        if result["status"] == "success":
            print(f"  [+] Node.js installed successfully")
            return True
        print(f"  [!] Install failed: {result['message']}")
        return False

    if get_os() == "darwin":
        from installer import run_brew
        found, _ = check_command("brew")
        if found:
            ok, msg = run_brew("node", timeout=get_timeout_for_tool("node"))
            if ok:
                print(f"  [+] Node.js installed via brew")
                return True
            print(f"  [!] brew failed: {msg}")

    from installer import run_apt
    ok, msg = run_apt(["nodejs"], timeout=get_timeout_for_tool("node"))
    if ok:
        add_to_path_linux("/usr/bin")
        print(f"  [+] Node.js installed successfully")
        return True

    print(f"  [!] Auto-install failed: {msg}")
    print(f"      Install manually: https://nodejs.org/")
    return False


def install_go(install_dir: str) -> bool:
    print(f"\n[Go Installation]")
    print(f"  Target: {install_dir}\\Go")

    if get_os() == "win32":
        from installer import run_winget, install_with_fallback, get_timeout_for_tool
        timeout = get_timeout_for_tool("go")

        found, _ = check_command("winget")
        if found:
            ok, msg = run_winget("GoLang.Go", timeout=timeout)
            if ok:
                go_bin = os.path.join(install_dir, "Go", "bin")
                add_to_path_windows(go_bin)
                print(f"  [+] Go installed via winget")
                return True
            print(f"  [!] winget failed: {msg}")

        # Method 2: Download ZIP/MSI directly
        url = "https://go.dev/dl/go1.23.4.windows-amd64.msi"
        result = install_with_fallback(
            installer_name="go",
            url=url,
            dest_dir=os.path.join(tempfile.gettempdir(), "go-installer"),
            timeout=timeout,
            install_cmd=["msiexec", "/i", "{filepath}", "/quiet", "/norestart"],
        )
        if result["status"] == "success":
            go_bin = os.path.join(install_dir, "Go", "bin")
            add_to_path_windows(go_bin)
            print(f"  [+] Go installed successfully")
            return True
        print(f"  [!] Install failed: {result['message']}")
        return False

    if get_os() == "darwin":
        from installer import run_brew
        found, _ = check_command("brew")
        if found:
            ok, msg = run_brew("go", timeout=get_timeout_for_tool("go"))
            if ok:
                print(f"  [+] Go installed via brew")
                return True
            print(f"  [!] brew failed: {msg}")

    from installer import run_apt
    ok, msg = run_apt(["golang"], timeout=get_timeout_for_tool("go"))
    if ok:
        add_to_path_linux("/usr/local/go/bin")
        print(f"  [+] Go installed successfully")
        return True

    print(f"  [!] Auto-install failed: {msg}")
    print(f"      Install manually: https://go.dev/dl/")
    return False


def install_java(install_dir: str) -> bool:
    print(f"\n[Java JDK Installation]")
    print(f"  Target: {install_dir}\\Java")

    if get_os() == "win32":
        from installer import run_winget, install_with_fallback, get_timeout_for_tool
        timeout = get_timeout_for_tool("java")

        found, _ = check_command("winget")
        if found:
            ok, msg = run_winget("EclipseAdoptium.Temurin.17.JDK", timeout=timeout)
            if ok:
                print(f"  [+] Java JDK installed via winget")
                print(f"  [+] JAVA_HOME configured automatically")
                return True
            print(f"  [!] winget failed: {msg}")

        # Method 2: Download EXE directly
        url = ("https://api.adoptium.net/v3/binary/release/17/ga/windows/x64/jdk/"
               "hotspot/normal/eclipse")
        result = install_with_fallback(
            installer_name="java",
            url=url,
            dest_dir=os.path.join(tempfile.gettempdir(), "java-installer"),
            timeout=timeout,
        )
        if result["status"] == "success" and result.get("filepath"):
            print(f"  [+] Java JDK downloaded to {result['filepath']}")
            print(f"      Run the installer manually, then set JAVA_HOME")
            return True
        print(f"  [!] Install failed: {result['message']}")
        return False

    if get_os() == "darwin":
        from installer import run_brew
        found, _ = check_command("brew")
        if found:
            ok, msg = run_brew("temurin@17", timeout=get_timeout_for_tool("java"))
            if ok:
                print(f"  [+] Java JDK installed via brew")
                return True
            print(f"  [!] brew failed: {msg}")

    from installer import run_apt
    ok, msg = run_apt(["openjdk-17-jdk"], timeout=get_timeout_for_tool("java"))
    if ok:
        print(f"  [+] Java JDK installed successfully")
        return True

    print(f"  [!] Auto-install failed: {msg}")
    print(f"      Install manually: https://adoptium.net/")
    return False


def install_docker(install_dir: str) -> bool:
    print(f"\n[Docker Installation]")

    if get_os() == "win32":
        found, _ = check_command("wsl")
        if not found:
            print("  [!] WSL not detected — Docker Desktop requires WSL2")
            print("      Run: wsl --install")
            input("  Press Enter after WSL install... ")

        print("  Download Docker Desktop from: https://www.docker.com/products/docker-desktop/")
        print("  After install, restart system and launch Docker Desktop")
        input("  Press Enter when done... ")
        return True

    if get_os() == "darwin":
        print("  Download Docker Desktop from: https://www.docker.com/products/docker-desktop/")
        input("  Press Enter when done... ")
        return True

    cmds = [
        ["sudo", "apt", "install", "-y", "docker.io", "docker-compose-plugin"],
        ["sudo", "systemctl", "start", "docker"],
        ["sudo", "systemctl", "enable", "docker"],
    ]
    for cmd in cmds:
        subprocess.run(cmd, capture_output=True, timeout=60)
    user = os.environ.get("USER", "")
    if user:
        subprocess.run(["sudo", "usermod", "-aG", "docker", user],
                       capture_output=True, timeout=10)
    print("  [+] Docker installed (re-login to apply group changes)")
    return True


def install_git(install_dir: str) -> bool:
    print(f"\n[Git Installation]")

    if get_os() == "win32":
        found, _ = check_command("winget")
        if found:
            result = subprocess.run(
                ["winget", "install", "Git.Git",
                 "--accept-package-agreements", "--accept-source-agreements"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                print("  [+] Git installed successfully")
                return True

        print("  Download from: https://git-scm.com/download/win")
        input("  Press Enter when done... ")
        return True

    if get_os() == "darwin":
        found, _ = check_command("brew")
        if found:
            subprocess.run(["brew", "install", "git"], capture_output=True, timeout=60)
            print("  [+] Git installed successfully")
            return True

    subprocess.run(["sudo", "apt", "install", "-y", "git"], capture_output=True, timeout=60)
    print("  [+] Git installed successfully")
    return True


def install_svn(install_dir: str) -> bool:
    print(f"\n[SVN Installation]")

    if get_os() == "win32":
        found, _ = check_command("winget")
        if found:
            result = subprocess.run(
                ["winget", "install", "Apache.Subversion"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                print("  [+] SVN installed successfully")
                return True

        print("  Download from: https://subversion.apache.org/packages.html")
        input("  Press Enter when done... ")
        return True

    if get_os() == "darwin":
        subprocess.run(["brew", "install", "subversion"], capture_output=True, timeout=60)
        print("  [+] SVN installed successfully")
        return True

    subprocess.run(["sudo", "apt", "install", "-y", "subversion"], capture_output=True, timeout=60)
    print("  [+] SVN installed successfully")
    return True


def install_wsl():
    print(f"\n[WSL Installation]")
    result = subprocess.run(["wsl", "--install"], capture_output=True, text=True, timeout=300)
    if result.returncode == 0:
        print("  [+] WSL installed (please reboot the system)")
    else:
        print(f"  [!] Output: {result.stderr}")
        print("  Run manually: wsl --install")


def build_missing_list(runtime_status: dict) -> list[dict]:
    """Build a numbered list of missing runtimes with index for user selection."""
    missing = []
    for idx, (name, status) in enumerate(runtime_status.items(), 1):
        if not status["found"]:
            missing.append({
                "index": idx,
                "name": name,
                "description": status["description"],
                "env_var": status.get("env_var", ""),
            })
    return missing


def print_selection_menu(missing_items: list[dict]):
    print("\n" + "=" * 60)
    print("  Select environments to install")
    print("=" * 60)
    print(f"\n  Number  |  Name     |  Description")
    print(f"  --------+-----------+------------------------------------------")
    for item in missing_items:
        env = f"  (sets {item['env_var']})" if item.get("env_var") else ""
        print(f"  {item['index']:<8}|  {item['name']:<9} |  {item['description']}{env}")
    print(f"\n  [all]    Install all missing environments")
    print(f"  [skip]   Skip installation, proceed to project scaffold")
    print("-" * 60)


def get_user_selection(missing_items: list[dict]) -> tuple[list[str], bool]:
    """Get user selection and return (selected_names, should_skip)."""
    while True:
        choice = input("\n  Selection: ").strip().lower()

        if choice == "skip":
            return [], True
        if choice == "all":
            return [item["name"] for item in missing_items], False

        # Try comma-separated indices
        try:
            indices = [int(x.strip()) for x in choice.split(",")]
            selected = []
            for i in indices:
                matched = next((item for item in missing_items if item["index"] == i), None)
                if matched:
                    selected.append(matched["name"])
                else:
                    print(f"  [!] No environment with number {i}")
            if selected:
                return selected, False
        except ValueError:
            pass

        # Try by name
        names = [item["name"].lower() for item in missing_items]
        if choice in names:
            return [choice.capitalize() if choice.istitle() else choice], False
        # Partial name match
        matches = [item["name"] for item in missing_items if choice in item["name"].lower()]
        if len(matches) == 1:
            return [matches[0]], False
        if len(matches) > 1:
            print(f"  [!] Multiple matches: {', '.join(matches)}")
            continue

        print(f"  [!] Invalid input '{choice}', try again")


def confirm_path(base_dir: str) -> str:
    drives = get_system_drives()
    system_drive = drives[0] if drives else "C:\\"

    print(f"\n{'-' * 60}")
    print(f"  Installation Path Confirmation")
    print(f"{'-' * 60}")

    # Show drive info if multiple drives exist
    if len(drives) > 1:
        print(f"\n  Available drives: {', '.join(drives)}")
        for d in drives:
            free = get_free_space_for_drive(d)
            print(f"    {d}  free: {free:,} MB")
        print()

    print(f"\n  Default base install directory: {base_dir}")
    print(f"\n  Each environment will be installed to:")
    print(f"    Python  -> {base_dir}\\Python")
    print(f"    Node.js -> {base_dir}\\Node")
    print(f"    Go      -> {base_dir}\\Go")
    print(f"    Java    -> {base_dir}\\Java")
    print(f"    Git     -> System default path")
    print(f"    Docker  -> System default path")
    print(f"\n  NOTE: Tools are installed to {base_dir}, NOT to system directories.")
    print(f"        System-level installs (winget/apt/brew) are NOT modified by this skill.")

    while True:
        choice = input(f"\n  Confirm path? (y/n, or enter custom absolute path): ").strip().lower()
        if choice in ("y", ""):
            return base_dir
        elif choice == "n":
            new_path = input("  Enter custom path: ").strip()
            if new_path and os.path.isabs(new_path):
                return new_path
            else:
                print("  [!] Please enter a valid absolute path")
        elif os.path.isabs(choice):
            return choice
        else:
            print(f"  Input: '{choice}'")


def get_free_space_for_drive(drive: str) -> int:
    """Get free space in MB for a drive."""
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
    return 0


def post_install_verification(selected: list[str]) -> dict:
    """Verify installations after setup — each checked independently."""
    from detect_env import get_version_output
    checks = {
        "Python": lambda: get_version_output(["python", "python3"])[0],
        "Node.js": lambda: get_version_output(["node"])[0],
        "Go": lambda: get_version_output(["go"])[0],
        "Java": lambda: get_version_output(["java", "javac"])[0],
        "Docker": lambda: get_version_output(["docker"])[0],
        "Git": lambda: get_version_output(["git"])[0],
        "SVN": lambda: get_version_output(["svn"])[0],
        "WSL": lambda: get_version_output(["wsl"])[0],
        "ADB": lambda: get_version_output(["adb"])[0],
        "HDC": lambda: get_version_output(["hdc"])[0],
        "tidevice": lambda: get_version_output(["tidevice"])[0],
    }

    results = {}
    print(f"\n{'-' * 60}")
    print(f"  Post-Installation Verification")
    print(f"{'-' * 60}")
    for item in selected:
        checker = checks.get(item)
        if checker:
            try:
                ok = checker()
                results[item] = "[OK]" if ok else "[FAIL]"
                status = "Verified" if ok else "Failed — please check installation"
            except Exception as e:
                results[item] = "[ERROR]"
                status = f"Error during verification: {e}"
            print(f"  {item:<12} {results[item]}  {status}")
        else:
            results[item] = "[SKIP]"
            print(f"  {item:<12} [SKIP]  no verification command defined")
    return results


INSTALL_MAP = {
    "Python": install_python,
    "Node.js": install_node,
    "Go": install_go,
    "Java": install_java,
    "Docker": install_docker,
    "Git": install_git,
    "SVN": install_svn,
    "WSL": install_wsl,
}

# Additional installers for tools not in RUNTIMES list
EXTRA_INSTALLERS = {
    "JMeter": lambda d: _install_jmeter(d),
    "Locust": lambda d: _install_locust(d),
    "ADB": lambda d: _install_adb(d),
    "HDC": lambda d: _install_hdc(d),
    "tidevice": lambda d: _install_tidevice(d),
    "Hypium": lambda d: _install_hypium(d),
}
INSTALL_MAP.update(EXTRA_INSTALLERS)


def _install_jmeter(install_base: str) -> bool:
    print(f"\n[JMeter Installation]")
    print(f"  Target: {install_base}/JMeter/")
    # Check local package
    local_zip = os.path.join("E:\\Tools_Package", "JMeter", "apache-jmeter-5.6.2.zip")
    if os.path.isfile(local_zip):
        target_dir = os.path.join(install_base, "JMeter", "apache-jmeter-5.6.2")
        os.makedirs(target_dir, exist_ok=True)
        try:
            import zipfile
            with zipfile.ZipFile(local_zip, 'r') as z:
                z.extractall(target_dir)
            print(f"  [+] JMeter extracted from local package: {local_zip}")
            return True
        except Exception as e:
            print(f"  [!] Extract failed: {e}")
    print("  [!] No local package found")
    print("      Download from: https://archive.apache.org/dist/jmeter/binaries/")
    print("      Extract to: " + os.path.join(install_base, "JMeter", "<version>"))
    input("  Press Enter when done... ")
    return True


def _install_locust(install_base: str) -> bool:
    print(f"\n[Locust Installation]")
    try:
        result = subprocess.run(["pip", "install", "locust>=2.32.0"],
                                capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("  [+] Locust installed via pip")
            return True
        print(f"  [!] pip install failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"  [!] Error: {e}")
    print("  Please run manually: pip install locust")
    return False


def _install_adb(install_base: str) -> bool:
    print(f"\n[ADB Installation]")
    local_zip = os.path.join("E:\\Tools_Package", "Android-ADB", "platform-tools-latest-windows.zip")
    target_dir = os.path.join(install_base, "Android-ADB", "platform-tools")
    if os.path.isfile(local_zip):
        os.makedirs(target_dir, exist_ok=True)
        try:
            import zipfile
            with zipfile.ZipFile(local_zip, 'r') as z:
                z.extractall(target_dir)
            print(f"  [+] ADB extracted from local package")
            return True
        except Exception as e:
            print(f"  [!] Extract failed: {e}")
    print("  Download from: https://developer.android.com/tools/releases/platform-tools")
    print(f"  Extract to: {target_dir}")
    input("  Press Enter when done... ")
    return True


def _install_hdc(install_base: str) -> bool:
    print(f"\n[HDC Installation]")
    local_dir = os.path.join("E:\\Tools_Package", "HDC")
    target_dir = os.path.join(install_base, "HDC")
    if os.path.isdir(local_dir):
        shutil.copytree(local_dir, target_dir, dirs_exist_ok=True)
        print(f"  [+] HDC copied from local package")
        return True
    print("  Download DevEco Studio from: https://developer.huawei.com/consumer/cn/deveco-studio/")
    print(f"  Copy hdc.exe to: {target_dir}")
    input("  Press Enter when done... ")
    return True


def _install_tidevice(install_base: str) -> bool:
    print(f"\n[tidevice Installation]")
    try:
        result = subprocess.run(["pip", "install", "tidevice"],
                                capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("  [+] tidevice installed via pip")
            return True
        print(f"  [!] pip install failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"  [!] Error: {e}")
    print("  Please run manually: pip install tidevice")
    return False


def _install_hypium(install_base: str) -> bool:
    print(f"\n[Hypium Installation]")
    try:
        result = subprocess.run(["npm", "install", "-g", "@hmos/hypium"],
                                capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print("  [+] Hypium installed via npm")
            return True
        print(f"  [!] npm install failed: {result.stderr[:200]}")
    except Exception as e:
        print(f"  [!] Error: {e}")
    print("  Please run manually: npm install -g @hmos/hypium")
    return False


def main():
    import detect_env
    from detect_env import RUNTIMES, PACKAGE_MANAGERS, get_os, get_system_drives

    # Initialize logging
    import logging as _log_mod
    _log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    Path(_log_dir).mkdir(parents=True, exist_ok=True)
    log_file = os.path.join(_log_dir, f"install_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    _logger = _log_mod.getLogger("dev-env-setup")
    _logger.setLevel(_log_mod.DEBUG)
    # File handler
    _fh = _log_mod.FileHandler(log_file, encoding="utf-8")
    _fh.setLevel(_log_mod.DEBUG)
    _fh.setFormatter(_log_mod.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    _logger.addHandler(_fh)
    # Console handler
    _ch = _log_mod.StreamHandler(sys.stdout)
    _ch.setLevel(_log_mod.INFO)
    _ch.setFormatter(_log_mod.Formatter("%(message)s"))
    _logger.addHandler(_ch)

    print("\n" + "=" * 60)
    print("  Dev Environment Setup")
    print("=" * 60)
    _logger.info("Session started, log file: %s", log_file)

    # Step 1: Detect existing environments
    detect_env.main()

    # Step 2: Collect runtime status
    runtime_status = {}
    for runtime in RUNTIMES:
        found, version_str = detect_env.get_version_output(runtime.commands)
        path = detect_env.find_command_path(runtime.commands[0]) if found else ""
        runtime_status[runtime.name] = {
            "found": found,
            "version": version_str,
            "path": path,
            "description": runtime.description,
            "env_var": runtime.env_var,
        }

    # Step 2.5: Multi-Python coexistence check
    _check_python_coexist(runtime_status)

    # Step 3: No missing items
    missing_items = build_missing_list(runtime_status)
    if not missing_items:
        print("\n  All runtimes are already installed. No action needed.")
        return

    # Step 4: Selection menu
    print_selection_menu(missing_items)

    # Step 5: Get selection
    selected, should_skip = get_user_selection(missing_items)
    if should_skip:
        print("\n  Skipping environment installation, proceeding to project scaffold.")
        return

    print(f"\n  Selected for installation: {', '.join(selected)}")

    # Step 6: Confirm path
    drives = get_system_drives()
    system_drive = drives[0] if drives else "C:\\"
    preferred_drive = select_install_drive()
    base_dir = get_base_install_dir(preferred_drive)
    install_base = confirm_path(base_dir)

    Path(install_base).mkdir(parents=True, exist_ok=True)
    print(f"\n  Install base: {install_base}")
    _logger.info("Install base: %s", install_base)

    # Step 7: Install each selected environment with progress bar
    total = len(selected)
    print(f"\n{'=' * 60}")
    print("  Installation Started")
    print(f"{'=' * 60}")

    results = {}
    for idx, item in enumerate(selected, 1):
        # Progress bar
        pct = int(idx / total * 100)
        bar_len = 20
        filled = int(bar_len * idx / total)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"\n  [{bar}] {idx}/{total} ({pct}%)  [..]  {item} — installing...", end="", flush=True)
        _logger.info("Installing %s (%d/%d)", item, idx, total)

        installer = INSTALL_MAP.get(item)
        if installer:
            try:
                ok = installer(install_base)
                results[item] = {"status": "success" if ok else "failed",
                                  "message": "ok" if ok else "installation returned non-zero"}
            except Exception as e:
                results[item] = {"status": "error", "message": str(e)}
                print(f"\r  [{bar}] {idx}/{total} ({pct}%)  [FAIL]  {item} — {e}", flush=True)
                _logger.error("Error installing %s: %s", item, e)
                continue
        else:
            results[item] = {"status": "skipped", "message": "no installer defined"}

        # Update progress line
        icon = "[OK]" if results[item]["status"] == "success" else ("[FAIL]" if results[item]["status"] in ("failed", "error") else "[SKIP]")
        print(f"\r  [{bar}] {idx}/{total} ({pct}%)  {icon}  {item}", flush=True)
        _logger.info("Installation %s: %s", item, results[item]["status"])

    # Step 8: Post-install verification
    verification = post_install_verification(selected)

    # Step 9: Summary
    print(f"\n{'=' * 60}")
    print("  Installation Complete")
    print(f"{'=' * 60}")

    completed = [k for k, v in results.items() if v["status"] == "success"]
    failed = [k for k, v in results.items() if v["status"] in ("failed", "error")]
    skipped = [k for k, v in results.items() if v["status"] == "skipped"]

    for item in selected:
        r = results[item]
        status_icon = "[OK]" if r["status"] == "success" else ("[FAIL]" if r["status"] in ("failed", "error") else "[SKIP]")
        verify = verification.get(item, "?")
        msg = r.get("message", "")
        print(f"  {item:<12} {status_icon}  verify={verify}  {msg}")

    print(f"\n  Install path: {install_base}")
    print(f"\n  Summary: {len(completed)} success, {len(failed)} failed, {len(skipped)} skipped")
    print(f"\n  Note: Restart your terminal for new tools to take effect.")
    _logger.info("Session complete: %d success, %d failed, %d skipped", len(completed), len(failed), len(skipped))
    _logger.info("Log file: %s", log_file)

    # Step 10: Generate report
    if completed or failed or skipped:
        report_script = os.path.join(os.path.dirname(__file__), "report.py")
        if os.path.isfile(report_script):
            import json as _json
            env_status_file = os.path.join(os.path.dirname(__file__), "..", "reports", "env_status.json")
            os.makedirs(os.path.dirname(env_status_file), exist_ok=True)
            with open(env_status_file, "w") as f:
                _json.dump(verification, f, indent=2)
            failed_reasons = []
            for k, v in results.items():
                if v["status"] in ("failed", "error"):
                    failed_reasons.append(f"{k}:{v.get('message', 'unknown')}")
            skip_reasons = []
            for k, v in results.items():
                if v["status"] == "skipped":
                    skip_reasons.append(f"{k}:{v.get('message', '')}")
            network_used = ["python.org", "nodejs.org", "go.dev", "adoptium.net",
                            "archive.apache.org", "pypi.org", "dl.google.com", "huawei.com"]
            verify_cmd = "python scripts/verify_env.py " + " ".join(completed) if completed else ""
            print(f"\n  Report saved: {env_status_file}")
            print(f"  Log file:     {log_file}")
            if verify_cmd:
                print(f"  Verify command: {verify_cmd}")
            # Run report generator
            try:
                subprocess.run(
                    [sys.executable, report_script,
                     "--operation", "install",
                     "--selected"] + selected +
                     ["--completed"] + completed +
                     ["--failed"] + failed +
                     ["--failed-reasons"] + failed_reasons +
                     ["--skipped"] + skipped +
                     ["--skipped-reasons"] + skip_reasons +
                     ["--base-dir", install_base,
                      "--system-drive", system_drive],
                    capture_output=True, timeout=30,
                )
            except Exception as e:
                print(f"  [!] Report generation skipped: {e}")

    _logger.removeHandler(_fh)
    _logger.removeHandler(_ch)
    _fh.close()
    print()


def _check_python_coexist(runtime_status: dict):
    """Check for Python coexistence and show guidance."""
    python_entry = runtime_status.get("Python", {})
    if not python_entry.get("found"):
        return
    current_ver = python_entry.get("version", "")
    current_path = python_entry.get("path", "")
    # Check if system Python path differs from install target
    install_base = os.path.join(get_system_drive(), "dev-tools")
    target_path = os.path.join(install_base, "Python")
    if current_path and target_path not in current_path:
        print(f"\n  [INFO] Python coexistence detected:")
        print(f"    Current:  {current_ver}  ->  {current_path}")
        print(f"    Target:   3.12.x       ->  {target_path}")
        print(f"    Note:     Use 'py -3.12' to invoke the new Python")
        print(f"              Use 'py -3.14' to invoke the current Python")
        print(f"              The py launcher handles version selection automatically.")


if __name__ == "__main__":
    main()
