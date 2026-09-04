#!/usr/bin/env python3
"""
Offline Package Locator and Integrity Checker
Checks E:\\Tools_Package\\ for cached installers, validates manifest.json,
and computes expected install sizes for pre-installation space estimation.
"""

import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PackageInfo:
    name: str
    local_path: Optional[str] = None       # path to local installer/archive
    local_sha256: Optional[str] = None     # expected SHA-256 from manifest
    official_url: Optional[str] = None     # official download URL
    official_sha256: Optional[str] = None  # official SHA-256 for verification
    size_bytes: int = 0                    # local archive size (0 = not local)
    disk: str = ""                         # drive letter of local file


OFFLINE_DIRS = [
    r"E:\Tools_Package",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Tools_Package"),
    os.path.join(os.environ.get("USERPROFILE", ""), "Tools_Package"),
]

MANIFEST_KEYS = {"name", "version", "files", "sha256"}


def sha256_file(path: str) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def get_disk(drive_path: str) -> str:
    """Extract drive letter from a path."""
    if drive_path and len(drive_path) >= 2 and drive_path[1] == ":":
        return drive_path[:2].upper()
    return ""


def get_free_space(drive: str) -> int:
    """Get free space in bytes for a drive."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"(Get-PSDrive -Name '{drive.rstrip(chr(58))}' -ErrorAction SilentlyContinue).Free"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return int(result.stdout.strip()) // (1024 * 1024)  # MB
    except Exception:
        pass
    return 0


def find_zip_files(base_dir: str) -> list[str]:
    """Find Tools_Package*.zip files in a directory."""
    if not os.path.isdir(base_dir):
        return []
    return [os.path.join(base_dir, f) for f in os.listdir(base_dir)
            if f.lower().startswith("tools_package") and f.lower().endswith(".zip")]


def load_manifest(manifest_path: str) -> Optional[dict]:
    """Load and validate manifest.json."""
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        missing = MANIFEST_KEYS - set(data.keys())
        if missing:
            return None
        return data
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        return None


def check_local_package(env_name: str) -> Optional[PackageInfo]:
    """Check if a local package exists for the given environment name."""
    for base_dir in OFFLINE_DIRS:
        tool_dir = os.path.join(base_dir, env_name)
        if not os.path.isdir(tool_dir):
            continue

        # Check for manifest.json
        manifest_path = os.path.join(tool_dir, "manifest.json")
        if os.path.isfile(manifest_path):
            manifest = load_manifest(manifest_path)
            if manifest is None:
                continue

            # Find the installer/archive file
            files = manifest.get("files", [])
            installer = None
            for f in files:
                full = os.path.join(tool_dir, f)
                if os.path.isfile(full):
                    installer = full
                    break

            if installer:
                size = os.path.getsize(installer)
                actual_sha = sha256_file(installer)
                expected_sha = manifest.get("sha256", "")
                return PackageInfo(
                    name=env_name,
                    local_path=installer,
                    local_sha256=actual_sha,
                    official_url=manifest.get("url"),
                    official_sha256=expected_sha,
                    size_bytes=size,
                    disk=get_disk(installer),
                )

    # Check for common archive formats without manifest
    for ext in [".zip", ".exe", ".msi"]:
        for base_dir in OFFLINE_DIRS:
            candidates = list(Path(base_dir).rglob(f"*{env_name.lower()}*{ext}"))
            if candidates:
                path = str(candidates[0])
                size = os.path.getsize(path)
                return PackageInfo(
                    name=env_name,
                    local_path=path,
                    size_bytes=size,
                    disk=get_disk(path),
                )

    return None


def estimate_install_size(package: PackageInfo, installed: bool) -> dict:
    """Estimate installation disk usage."""
    if installed:
        return {
            "download_mb": 0,
            "install_mb": 0,
            "temp_mb": 0,
            "total_mb": 0,
            "note": "Already installed, no new space needed",
        }

    if not package or not package.local_path:
        return {
            "download_mb": 0,
            "install_mb": 0,
            "temp_mb": 0,
            "total_mb": 0,
            "note": "No local package; online download size unknown until fetched",
        }

    size_mb = package.size_bytes // (1024 * 1024)
    # Installer temp space: roughly same as archive size for ZIP, 1.5x for EXE
    is_executable = package.local_path.lower().endswith((".exe", ".msi"))
    temp_ratio = 1.5 if is_executable else 1.0
    temp_mb = int(size_mb * temp_ratio)
    # Install size: estimate based on tool type
    install_ratio = 2.0 if is_executable else 1.0  # EXE installs to more dirs
    install_mb = int(size_mb * install_ratio)
    total_mb = size_mb + temp_mb + install_mb

    return {
        "download_mb": size_mb,
        "install_mb": install_mb,
        "temp_mb": temp_mb,
        "total_mb": total_mb,
        "note": f"Local package: {package.local_path}",
    }


def check_disk_space(drive: str, required_mb: int) -> tuple[bool, int, int]:
    """Check if a drive has enough free space."""
    free_mb = get_free_space(drive)
    return free_mb >= required_mb, free_mb, required_mb


def print_package_status(env_name: str, package: Optional[PackageInfo]):
    """Print package status for an environment."""
    if package:
        status = "LOCAL"
        size_mb = package.size_bytes // (1024 * 1024)
        sha_match = "SHA OK" if package.local_sha256 and package.official_sha256 and package.local_sha256 == package.official_sha256 else "SHA UNKNOWN"
        print(f"  [{env_name:<15}] [{status:<8}] {size_mb:>5} MB  {sha_match}  {package.local_path}")
    else:
        print(f"  [{env_name:<15}] [ONLINE]  Will download from official source")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check local offline packages for dev environments")
    parser.add_argument("envs", nargs="+", help="Environment names to check (e.g. Python Go JMeter)")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    results = {}
    print("-" * 60)
    print("  Offline Package Check")
    print("-" * 60)
    print()

    for env_name in args.envs:
        pkg = check_local_package(env_name.capitalize())
        results[env_name] = pkg
        print_package_status(env_name, pkg)

    print()
    print("-" * 60)

    if args.json:
        json_results = {k: {
            "found": v is not None,
            "path": v.local_path if v else None,
            "size_mb": v.size_bytes // (1024 * 1024) if v else 0,
            "disk": v.disk if v else "",
            "sha256": v.local_sha256 if v else None,
        } for k, v in results.items()}
        print(json.dumps(json_results, indent=2))


if __name__ == "__main__":
    main()
