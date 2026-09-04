#!/usr/bin/env python3
"""
Logging utility for dev environment setup.
Provides both console output and persistent log file per session.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path


_LOG_DIR = None
_LOGGER = None


def init_log_dir(base_dir: str = None) -> str:
    """Initialize log directory. Returns path to log directory."""
    global _LOG_DIR
    if _LOG_DIR:
        return _LOG_DIR
    if base_dir:
        _LOG_DIR = os.path.join(base_dir, "logs")
    else:
        _LOG_DIR = os.path.join(os.getcwd(), "logs")
    Path(_LOG_DIR).mkdir(parents=True, exist_ok=True)
    return _LOG_DIR


def get_log_file(operation: str = "install") -> str:
    """Get path to current session's log file."""
    if not _LOG_DIR:
        init_log_dir()
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(_LOG_DIR, f"log_{operation}_{now_str}.txt")


def get_logger(operation: str = "install", log_file: str = None) -> logging.Logger:
    """Get or create a logger that writes to both console and file."""
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER

    logger = logging.getLogger(f"dev-env-{operation}")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler — always INFO+
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    chFormatter = logging.Formatter("%(message)s")
    ch.setFormatter(chFormatter)
    logger.addHandler(ch)

    # File handler — DEBUG level, one per session
    if not log_file:
        log_file = get_log_file(operation)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fhFormatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(fhFormatter)
    logger.addHandler(fh)

    _LOGGER = logger
    return logger


def log(operation: str = "install", message: str = "", level: str = "INFO"):
    """Convenience function to log a message."""
    logger = get_logger(operation)
    getattr(logger, level.lower(), logger.info)(message)
    return logger


def log_step(operation: str, current: int, total: int, env_name: str, status: str):
    """Log a step in the installation with progress indicator."""
    pct = int(current / total * 100) if total > 0 else 0
    bar_len = 20
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = "#" * filled + "-" * (bar_len - filled)
    status_icon = {"success": "[OK]", "failed": "[FAIL]", "skipped": "[SKIP]", "running": "[..]"}.get(status, "[..]")
    msg = f"  [{bar}] {current}/{total} ({pct}%)  {status_icon}  {env_name}"
    logger = get_logger(operation)
    logger.info(msg)
    return msg


def close_log():
    """Close all log handlers and reset singleton."""
    global _LOGGER
    if _LOGGER:
        for h in _LOGGER.handlers[:]:
            h.close()
            _LOGGER.removeHandler(h)
        _LOGGER = None


def get_latest_log(operation: str = "install") -> str:
    """Get path to the most recent log file for an operation."""
    if not _LOG_DIR:
        return ""
    log_dir = init_log_dir()
    prefix = f"log_{operation}_"
    logs = sorted(
        [f for f in os.listdir(log_dir) if f.startswith(prefix) and f.endswith(".txt")],
        reverse=True,
    )
    return os.path.join(log_dir, logs[0]) if logs else ""


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Dev environment logging utility")
    parser.add_argument("--init", action="store_true", help="Initialize log directory")
    parser.add_argument("--operation", default="install", choices=["install", "uninstall"])
    parser.add_argument("--list", action="store_true", help="List available log files")
    args = parser.parse_args()

    if args.init:
        path = init_log_dir()
        print(f"Log directory: {path}")
    elif args.list:
        log_dir = init_log_dir()
        prefix = f"log_{args.operation}_"
        logs = sorted(
            [f for f in os.listdir(log_dir) if f.startswith(prefix)],
            reverse=True,
        )
        if logs:
            for f in logs:
                full = os.path.join(log_dir, f)
                size = os.path.getsize(full)
                print(f"  {f}  ({size:,} bytes)")
        else:
            print("  No logs found")
    else:
        print("Usage: python scripts/logging.py --init | --list")


if __name__ == "__main__":
    main()
