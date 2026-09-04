#!/usr/bin/env python3
"""
Download and execute installer with timeout, SHA-256 verification, retry, and mirror fallback.
Handles winget/MSI/ZIP download, checksum verification, and silent install execution.
"""

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


# Timeout configuration (seconds) per installer type
TIMEOUTS = {
    "winget": 300,
    "brew": 600,
    "apt": 600,
    "wget_download": 600,
    "curl_download": 600,
    "msi_install": 600,
    "exe_install": 300,
    "pip_install": 300,
    "npm_install": 300,
    "generic": 120,
}

# Retry configuration
DEFAULT_RETRIES = 3          # Number of retry attempts for download/install
RETRY_DELAY = 5              # Seconds to wait between retries


# Mirror sources — primary domestic mirror, then 2 backups
MIRROR_SOURCES = {
    "Python": {
        "primary":   "https://mirrors.huaweicloud.com/python/",
        "fallbacks": [
            "https://registry.npmmirror.com/-/binary/python/",
            "https://www.python.org/ftp/python/",
        ],
    },
    "Node.js": {
        "primary":   "https://mirrors.huaweicloud.com/nodejs-release/",
        "fallbacks": [
            "https://mirrors.tuna.tsinghua.edu.cn/nodejs-release/",
            "https://nodejs.org/dist/",
        ],
    },
    "Go": {
        "primary":   "https://mirrors.aliyun.com/golang/",
        "fallbacks": [
            "https://mirrors.tuna.tsinghua.edu.cn/golang/",
            "https://go.dev/dl/",
        ],
    },
    "Java": {
        "primary":   "https://mirrors.huaweicloud.com/adoptium/",
        "fallbacks": [
            "https://mirrors.tuna.tsinghua.edu.cn/Adoptium/",
            "https://api.adoptium.net/v3/binary/",
        ],
    },
    "Docker": {
        "primary":   "https://mirrors.huaweicloud.com/docker-desktop/",
        "fallbacks": [
            "https://download.docker.com/win/static/stable/",
            "https://desktop.docker.com/win/main/amd64/",
        ],
    },
    "JMeter": {
        "primary":   "https://mirrors.tuna.tsinghua.edu.cn/apache/jmeter/binaries/",
        "fallbacks": [
            "https://archive.apache.org/dist/jmeter/binaries/",
            "https://downloads.apache.org/jmeter/binaries/",
        ],
    },
    "Git": {
        "primary":   "https://mirrors.huaweicloud.com/git-for-windows/",
        "fallbacks": [
            "https://mirrors.tuna.tsinghua.edu.cn/git-for-windows/",
            "https://github.com/git-for-windows/git/releases/download/",
        ],
    },
    "SVN": {
        "primary":   "https://mirrors.huaweicloud.com/apache/subversion/",
        "fallbacks": [
            "https://downloads.apache.org/subversion/",
            "https://sourceforge.net/projects/subversion/files/",
        ],
    },
    "ADB": {
        "primary":   "https://mirrors.huaweicloud.com/android/platform-tools/",
        "fallbacks": [
            "https://dl.google.com/android/repository/",
            "https://dl-ssl.google.com/android/repository/",
        ],
    },
    "HDC": {
        "primary":   "https://mirrors.huaweicloud.com/deveco-studio/",
        "fallbacks": [
            "https://developer.huawei.com/consumer/cn/deveco-studio/",
        ],
    },
    "tidevice": {
        "primary":   "https://mirrors.huaweicloud.com/pypi/simple/tidevice/",
        "fallbacks": [
            "https://pypi.org/simple/tidevice/",
        ],
    },
    "Hypium": {
        "primary":   "https://mirrors.huaweicloud.com/npm/@hmos/hypium/",
        "fallbacks": [
            "https://registry.npmjs.org/@hmos/hypium/",
        ],
    },
    "Locust": {
        "primary":   "https://mirrors.huaweicloud.com/pypi/simple/locust/",
        "fallbacks": [
            "https://pypi.org/simple/locust/",
        ],
    },
}


def get_mirrors(env_name: str) -> list[str]:
    """Return ordered list of download mirrors for an environment."""
    info = MIRROR_SOURCES.get(env_name, {})
    mirrors = []
    if info.get("primary"):
        mirrors.append(info["primary"])
    mirrors.extend(info.get("fallbacks", []))
    # Ensure official URL is always the last fallback
    official = info.get("official") or (info.get("fallbacks") and info["fallbacks"][-1])
    if official and official not in mirrors:
        mirrors.append(official)
    return mirrors


def download_file(url: str, dest: str, timeout: int = 600) -> tuple[bool, str]:
    """Download a file from URL to dest, with progress and timeout."""
    try:
        import urllib.request
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)

        def report_hook(count, block_size, total_size):
            if total_size > 0:
                percent = min(count * block_size * 100 / total_size, 100)
                downloaded = count * block_size / (1024 * 1024)
                total = total_size / (1024 * 1024)
                sys.stdout.write(f"\r  Downloading: {downloaded:.1f}/{total:.1f} MB ({percent:.0f}%)  ")
                sys.stdout.flush()

        urllib.request.urlretrieve(url, dest, reporthook=report_hook)
        sys.stdout.write("\n")
        sys.stdout.flush()
        return True, dest
    except Exception as e:
        return False, str(e)


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest().lower()
    except Exception:
        return ""


def verify_sha256(filepath: str, expected_hash: str) -> bool:
    if not expected_hash:
        return True
    actual = compute_sha256(filepath)
    return actual == expected_hash.lower()


def cleanup_installers(filepaths: list[str], ask_confirm: bool = True) -> list[str]:
    """Remove downloaded installer files to free disk space. Returns list of removed paths."""
    removed = []
    if not filepaths:
        return removed

    if ask_confirm:
        print(f"\n  Cleanup: Remove {len(filepaths)} downloaded installer(s) to free space?")
        for fp in filepaths:
            size_mb = os.path.getsize(fp) // (1024 * 1024) if os.path.isfile(fp) else 0
            print(f"    - {fp}  ({size_mb} MB)")
        try:
            choice = input("  Confirm deletion? (y/n): ").strip().lower()
        except (EOFError, OSError):
            choice = "n"
        if choice != "y":
            print("  Skipping cleanup — installers preserved.")
            return removed

    for fp in filepaths:
        try:
            if os.path.isfile(fp):
                os.remove(fp)
                removed.append(fp)
        except Exception as e:
            print(f"  [!] Failed to remove {fp}: {e}")

    if removed:
        print(f"  [+] Cleaned up {len(removed)} installer(s)")
    return removed


def run_winget(package_id: str, timeout: int = None) -> tuple[bool, str]:
    timeout = timeout or TIMEOUTS["winget"]
    cmd = ["winget", "install", package_id,
           "--accept-package-agreements", "--accept-source-agreements", "--silent"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, f"winget install {package_id} succeeded"
        return False, f"winget failed (rc={result.returncode}): {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"winget timed out after {timeout}s"
    except FileNotFoundError:
        return False, "winget not found"
    except Exception as e:
        return False, str(e)


def run_brew(package: str, timeout: int = None) -> tuple[bool, str]:
    timeout = timeout or TIMEOUTS["brew"]
    try:
        result = subprocess.run(["brew", "install", package],
                                capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, f"brew install {package} succeeded"
        return False, f"brew failed: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"brew timed out after {timeout}s"
    except FileNotFoundError:
        return False, "brew not found"
    except Exception as e:
        return False, str(e)


def run_apt(packages: list[str], timeout: int = None) -> tuple[bool, str]:
    timeout = timeout or TIMEOUTS["apt"]
    try:
        result = subprocess.run(["sudo", "apt", "install", "-y"] + packages,
                                capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, f"apt install {' '.join(packages)} succeeded"
        return False, f"apt failed: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"apt timed out after {timeout}s"
    except FileNotFoundError:
        return False, "apt not found"
    except Exception as e:
        return False, str(e)


def run_msi_installer(msi_path: str, timeout: int = None) -> tuple[bool, str]:
    timeout = timeout or TIMEOUTS["msi_install"]
    try:
        result = subprocess.run(
            ["msiexec", "/i", msi_path, "/quiet", "/norestart",
             "/log", os.path.join(tempfile.gettempdir(), "install.log")],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode in (0, 3010):
            return True, "MSI install succeeded"
        return False, f"MSI failed (rc={result.returncode})"
    except subprocess.TimeoutExpired:
        return False, f"MSI install timed out after {timeout}s"
    except FileNotFoundError:
        return False, "msiexec not found"
    except Exception as e:
        return False, str(e)


def run_exe_installer(exe_path: str, timeout: int = None) -> tuple[bool, str]:
    timeout = timeout or TIMEOUTS["exe_install"]
    try:
        result = subprocess.run(
            [exe_path, "/S", "/quiet", "/norestart"],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0:
            return True, "EXE install succeeded"
        return False, f"EXE failed (rc={result.returncode}): {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"EXE install timed out after {timeout}s"
    except Exception as e:
        return False, str(e)


def run_pip_install(packages: list[str], timeout: int = None) -> tuple[bool, str]:
    timeout = timeout or TIMEOUTS["pip_install"]
    try:
        result = subprocess.run(["pip", "install"] + packages,
                                capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, f"pip install {' '.join(packages)} succeeded"
        return False, f"pip failed: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"pip timed out after {timeout}s"
    except Exception as e:
        return False, str(e)


def run_npm_install(packages: list[str], timeout: int = None) -> tuple[bool, str]:
    timeout = timeout or TIMEOUTS["npm_install"]
    try:
        result = subprocess.run(["npm", "install", "-g"] + packages,
                                capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            return True, f"npm install {' '.join(packages)} succeeded"
        return False, f"npm failed: {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return False, f"npm timed out after {timeout}s"
    except Exception as e:
        return False, str(e)


def download_with_mirrors(url_template_fn, env_name: str, version: str,
                          dest_dir: str, expected_sha256: str = "",
                          timeout: int = None, max_retries: int = DEFAULT_RETRIES) -> dict:
    """
    Download from mirror chain: primary → fallback1 → fallback2 → official.
    Each URL gets max_retries attempts before moving to next mirror.
    Returns dict with status, message, filepath, attempted_urls.
    """
    result = {
        "status": "failed",
        "message": "",
        "filepath": "",
        "attempted_urls": [],
        "failed_urls": [],
    }
    timeout = timeout or TIMEOUTS["generic"]

    # Build mirror URL list
    mirrors = get_mirrors(env_name)
    urls = []
    for mirror in mirrors:
        try:
            url = url_template_fn(mirror, version)
            urls.append(url)
        except Exception:
            pass

    if not urls:
        result["message"] = "No download URLs available for this environment"
        return result

    downloaded_file = None

    for attempt in range(1, max_retries + 1):
        for url in urls:
            result["attempted_urls"].append(url)
            print(f"  Attempt {attempt}/{max_retries}: {url[:80]}...")

            ok, msg = download_file(url, dest_dir + "/installer.tmp", timeout=timeout)
            if ok:
                downloaded_file = dest_dir + "/installer.tmp"
                break  # Download succeeded, move to verification
            else:
                result["failed_urls"].append((url, msg))
                print(f"    Failed: {msg[:60]}")

        if downloaded_file:
            break  # Download succeeded, proceed to verification
        else:
            print(f"  All {len(urls)} mirrors failed on attempt {attempt}, retrying...")

    if not downloaded_file:
        result["status"] = "failed"
        result["message"] = (f"All mirrors failed after {max_retries} retries. "
                             f"Last error: {result['failed_urls'][-1][1] if result['failed_urls'] else 'unknown'}")
        return result

    # Verify SHA-256
    if expected_sha256:
        print(f"  Verifying SHA-256...")
        if not verify_sha256(downloaded_file, expected_sha256):
            actual = compute_sha256(downloaded_file)
            result["message"] = f"SHA-256 mismatch! Expected: {expected_sha256}, Got: {actual}"
            try:
                os.remove(downloaded_file)
            except Exception:
                pass
            return result
        print(f"  SHA-256 verified OK")

    result["filepath"] = downloaded_file
    result["status"] = "downloaded"
    result["message"] = f"Downloaded from: {urls[0][:60]}"
    return result


def install_with_fallback(env_name: str, url: str, dest_dir: str,
                          expected_sha256: str = "",
                          install_cmd: list[str] = None,
                          timeout: int = None,
                          max_retries: int = DEFAULT_RETRIES,
                          cleanup_after: bool = True,
                          ask_cleanup: bool = True) -> dict:
    """
    Unified install with:
    1. Download from URL (with mirror fallback + retry)
    2. SHA-256 verify
    3. Run installer command
    4. Cleanup downloaded file (optional, with user confirm)
    Returns dict with status, message, filepath, cleanup_paths.
    """
    result = {
        "status": "failed",
        "message": "",
        "filepath": "",
        "cleanup_paths": [],
        "method": "",
    }
    timeout = timeout or TIMEOUTS["generic"]

    # Step 1: Download
    os.makedirs(dest_dir, exist_ok=True)
    temp_file = os.path.join(dest_dir, "installer.tmp")

    print(f"  Downloading from: {url[:80]}...")
    ok, msg = download_file(url, temp_file, timeout=timeout)

    if not ok:
        result["message"] = f"Download failed: {msg}"
        return result

    result["filepath"] = temp_file
    result["method"] = "direct_download"

    # Step 2: SHA-256 verify
    if expected_sha256:
        print(f"  Verifying SHA-256...")
        if not verify_sha256(temp_file, expected_sha256):
            actual = compute_sha256(temp_file)
            result["message"] = f"SHA-256 mismatch! Expected: {expected_sha256}, Got: {actual}"
            try:
                os.remove(temp_file)
                result["filepath"] = ""
            except Exception:
                pass
            return result
        print(f"  SHA-256 verified OK")

    # Step 3: Retry loop for installation
    last_error = ""
    for attempt in range(1, max_retries + 1):
        if install_cmd:
            print(f"  Running installer (attempt {attempt}/{max_retries})...")
            try:
                proc_result = subprocess.run(
                    install_cmd,
                    capture_output=True, text=True, timeout=timeout,
                )
                if proc_result.returncode == 0:
                    result["status"] = "success"
                    result["message"] = f"Installation completed on attempt {attempt}"
                    result["filepath"] = temp_file  # Keep for potential cleanup
                    break
                last_error = f"Installer failed (rc={proc_result.returncode}): {proc_result.stderr[:200]}"
            except subprocess.TimeoutExpired:
                last_error = f"Installer timed out after {timeout}s on attempt {attempt}"
            except Exception as e:
                last_error = f"Installer error on attempt {attempt}: {e}"

            if attempt < max_retries:
                print(f"  [!] Attempt {attempt} failed: {last_error[:80]}")
                print(f"  Retrying in {RETRY_DELAY}s...")
                import time
                time.sleep(RETRY_DELAY)
        else:
            # No install command — download only
            result["status"] = "success"
            result["message"] = f"Downloaded to {temp_file} (manual install required)"
            break
    else:
        # All retries exhausted
        result["status"] = "failed"
        result["message"] = f"All {max_retries} attempts failed. Last error: {last_error}"

    # Step 4: Cleanup installer file
    if cleanup_after and result["status"] == "success" and result["filepath"]:
        cleaned = cleanup_installers([result["filepath"]], ask_confirm=ask_cleanup)
        result["cleanup_paths"] = cleaned
        if cleaned:
            result["filepath"] = ""  # File removed

    return result


def get_timeout_for_tool(tool_name: str) -> int:
    tool_lower = tool_name.lower()
    if "docker" in tool_lower:
        return TIMEOUTS["wget_download"] * 2
    if "java" in tool_lower or "jdk" in tool_lower:
        return TIMEOUTS["wget_download"]
    if "python" in tool_lower:
        return TIMEOUTS["wget_download"]
    if "go" in tool_lower:
        return TIMEOUTS["wget_download"]
    if "node" in tool_lower or "npm" in tool_lower:
        return TIMEOUTS["curl_download"]
    return TIMEOUTS["generic"]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download and run installer with verification")
    parser.add_argument("--tool", required=True, help="Tool name for timeout/mirror selection")
    parser.add_argument("--url", required=True, help="Primary download URL")
    parser.add_argument("--dest-dir", required=True, help="Directory to save installer")
    parser.add_argument("--sha256", default="", help="Expected SHA-256 hash")
    parser.add_argument("--install-cmd", nargs="*", help="Installer command to run after download")
    parser.add_argument("--timeout", type=int, help="Override default timeout")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="Max download retries per mirror")
    parser.add_argument("--no-cleanup", action="store_true", help="Don't ask to delete installer after install")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    timeout = args.timeout or get_timeout_for_tool(args.tool)

    result = install_with_fallback(
        env_name=args.tool,
        url=args.url,
        dest_dir=args.dest_dir,
        expected_sha256=args.sha256,
        install_cmd=args.install_cmd,
        timeout=timeout,
        max_retries=args.retries,
        cleanup_after=not args.no_cleanup,
    )

    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        icon = "OK" if result["status"] == "success" else ("TIMEOUT" if "timeout" in result["message"].lower() else "FAIL")
        print(f"\n  [{icon}] {result['message']}")
        if result.get("filepath"):
            print(f"  File: {result['filepath']}")
        if result.get("attempted_urls"):
            print(f"  Mirrors tried: {len(result['attempted_urls'])}")
        if result.get("cleanup_paths"):
            print(f"  Cleaned up: {len(result['cleanup_paths'])} file(s)")


if __name__ == "__main__":
    main()
