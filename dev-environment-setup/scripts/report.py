#!/usr/bin/env python3
"""
Environment Report Generator
Generates a complete report for install/uninstall operations.
Includes: process log, summary, environment status, env var changes, next steps.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def generate_report(
    operation: str,           # "install" or "uninstall"
    selected_envs: list[str],
    completed_envs: list[str],
    failed_envs: list[dict],     # [{"name": ..., "reason": ...}]
    skipped_envs: list[dict],    # [{"name": ..., "reason": ...}]
    env_status: dict,            # {"Python": "PASS", "Go": "FAIL", ...}
    env_vars_changed: list[dict], # [{"env": ..., "var": ..., "value": ...}]
    network_used: list[str],
    base_dir: str,
    system_drive: str,
):
    """Generate a structured report dict."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(selected_envs)
    success = len(completed_envs)
    failed = len(failed_envs)
    skipped = len(skipped_envs)

    report = {
        "operation": operation,
        "timestamp": now,
        "base_dir": base_dir,
        "system_drive": system_drive,
        "summary": {
            "total_requested": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "status": "PARTIAL" if (failed > 0 or skipped > 0) and success > 0
                      else "SUCCESS" if success == total and failed == 0
                      else "FAILED",
        },
        "details": {
            "completed": completed_envs,
            "failed": failed_envs,
            "skipped": skipped_envs,
            "environment_status": env_status,
            "env_vars_changed": env_vars_changed,
            "network_sources": network_used,
        },
        "next_steps": _generate_next_steps(operation, completed_envs, failed_envs, skipped_envs),
    }
    return report


def _generate_next_steps(op: str, completed: list, failed: list, skipped: list) -> list[str]:
    steps = []
    if op == "install":
        if completed:
            steps.append(f"已安装: {', '.join(completed)}")
            steps.append("请重新打开终端以使新环境变量生效")
        if failed:
            for f in failed:
                steps.append(f"安装失败 — {f['name']}: {f.get('reason', '未知原因')}")
                steps.append(f"  重试命令: python scripts/setup_env.py (手动选择 {f['name']})")
        if skipped:
            for s in skipped:
                steps.append(f"跳过 — {s['name']}: {s.get('reason', '')}")
        steps.append("")
        steps.append("验证命令: python scripts/verify_env.py " + " ".join(completed))
        steps.append("查看完整报告: 保存本报告的 JSON 文件")
    elif op == "uninstall":
        if completed:
            steps.append(f"已卸载: {', '.join(completed)}")
        if failed:
            for f in failed:
                steps.append(f"卸载失败 — {f['name']}: {f.get('reason', '未知原因')}")
        steps.append("")
        steps.append("建议: 重启终端并运行 detect_env.py 确认卸载结果")
    return steps


def print_report(report: dict):
    """Print a human-readable report."""
    s = report["summary"]
    d = report["details"]

    print("\n" + "=" * 70)
    print(f"  {report['operation'].upper()} REPORT")
    print("=" * 70)
    print(f"\n  Time:       {report['timestamp']}")
    print(f"  Base dir:   {report['base_dir']}")
    print(f"  System:     {report['system_drive']}")

    print(f"\n  ┌─────────────────────────────┐")
    print(f"  │  Summary                     │")
    print(f"  ├─────────────────────────────┤")
    print(f"  │  Requested: {s['total_requested']:>3}            │")
    print(f"  │  Success:   {s['success']:>3}            │")
    print(f"  │  Failed:    {s['failed']:>3}            │")
    print(f"  │  Skipped:   {s['skipped']:>3}            │")
    print(f"  │  Status:    {s['status']:>3}            │")
    print(f"  └─────────────────────────────┘")

    # Environment status
    if d["environment_status"]:
        print("\n  Environment Status:")
        for name, status in d["environment_status"].items():
            icon = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "?")
            print(f"    {icon}  {name:<15} {status}")

    # Completed
    if d["completed"]:
        print(f"\n  Completed ({len(d['completed'])}):")
        for name in d["completed"]:
            print(f"    [+] {name}")

    # Failed
    if d["failed"]:
        print(f"\n  Failed ({len(d['failed'])}):")
        for f in d["failed"]:
            reason = f.get("reason", "unknown")
            print(f"    [-] {f['name']:<15} {reason}")

    # Skipped
    if d["skipped"]:
        print(f"\n  Skipped ({len(d['skipped'])}):")
        for s in d["skipped"]:
            reason = s.get("reason", "")
            print(f"    [~] {s['name']:<15} {reason}")

    # Env var changes
    if d["env_vars_changed"]:
        print(f"\n  Environment Variables Changed ({len(d['env_vars_changed'])}):")
        for ev in d["env_vars_changed"]:
            print(f"    {ev['env']}: {ev['var']} = {ev['value'][:60]}")

    # Network
    if d["network_sources"]:
        print(f"\n  Network Sources Used:")
        for src in d["network_sources"]:
            print(f"    • {src}")

    # Next steps
    if report.get("next_steps"):
        print("\n  Next Steps:")
        for step in report["next_steps"]:
            print(f"    {step}")

    print("\n" + "=" * 70 + "\n")


def save_report(report: dict, output_dir: Optional[str] = None) -> str:
    """Save report to JSON file and HTML file."""
    if output_dir is None:
        output_dir = os.path.join(os.getcwd(), "reports")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    basename = f"report_{report['operation']}_{now_str}"

    # Save JSON
    json_path = os.path.join(output_dir, basename + ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Save HTML
    html_path = os.path.join(output_dir, basename + ".html")
    html_content = generate_html_report(report)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_path  # Return HTML path as primary report file


def generate_html_report(report: dict) -> str:
    """Generate a styled HTML report from report data."""
    s = report["summary"]
    d = report["details"]
    op = report["operation"].upper()
    status_color = {"SUCCESS": "#28a745", "PARTIAL": "#ffc107", "FAILED": "#dc3545"}.get(s["status"], "#6c757d")

    # Build table rows
    env_rows = ""
    for name, status in d.get("environment_status", {}).items():
        icon = "✓" if status == "PASS" else ("✗" if status == "FAIL" else "?")
        color = "#28a745" if status == "PASS" else ("#dc3545" if status == "FAIL" else "#ffc107")
        env_rows += '<tr><td>' + icon + '</td><td style="color:' + color + ';font-weight:bold">' + status + '</td><td>' + name + '</td></tr>\n'

    completed_rows = ""
    for name in d.get("completed", []):
        completed_rows += '<tr><td>✅</td><td>' + name + '</td><td>已安装/已验证</td></tr>\n'

    failed_rows = ""
    for item in d.get("failed", []):
        failed_rows += '<tr><td>❌</td><td>' + item["name"] + '</td><td>' + item.get("reason", "unknown") + '</td></tr>\n'

    skipped_rows = ""
    for item in d.get("skipped", []):
        skipped_rows += '<tr><td>⏭</td><td>' + item["name"] + '</td><td>' + item.get("reason", "") + '</td></tr>\n'

    envvar_rows = ""
    for ev in d.get("env_vars_changed", []):
        envvar_rows += '<tr><td>' + ev["env"] + '</td><td>' + ev["var"] + '</td><td style="font-size:12px">' + ev["value"] + '</td></tr>\n'

    network_items = "".join('<li>' + src + '</li>' for src in d.get("network_sources", []))
    steps_items = "".join('<li>' + step + '</li>' for step in report.get("next_steps", []))

    return _render_html_report(report, s, d, status_color, env_rows, completed_rows, failed_rows,
                                skipped_rows, envvar_rows, network_items, steps_items)
def _render_html_report(report, s, d, status_color, env_rows, completed_rows, failed_rows,
                         skipped_rows, envvar_rows, network_items, steps_items):
    """Actually render the HTML report with conditional sections."""
    parts = ['<!DOCTYPE html>', '<html lang="zh-CN">', '<head>',
              '<meta charset="UTF-8">', '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
              f'<title>{report["operation"].upper()} Report — {report["timestamp"]}</title>',
              '<style>',
              '* { margin: 0; padding: 0; box-sizing: border-box; }',
              'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f7fa; color: #333; padding: 24px; }',
              '.container { max-width: 900px; margin: 0 auto; }',
              '.card { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); padding: 24px; margin-bottom: 20px; }',
              '.header { text-align: center; padding: 32px 24px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border-radius: 12px; margin-bottom: 20px; }',
              '.header h1 { font-size: 28px; margin-bottom: 8px; }',
              '.header .op { font-size: 14px; opacity: 0.8; text-transform: uppercase; letter-spacing: 2px; }',
              f'.status-badge {{ display: inline-block; padding: 6px 20px; border-radius: 20px; font-size: 16px; font-weight: bold; color: #fff; margin-top: 12px; background: {status_color}; }}',
              '.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }',
              '.stat { background: #fff; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }',
              '.stat .num { font-size: 32px; font-weight: bold; }',
              '.stat .label { font-size: 13px; color: #888; margin-top: 4px; }',
              '.stat.success .num { color: #28a745; }',
              '.stat.failed .num { color: #dc3545; }',
              '.stat.skipped .num { color: #ffc107; }',
              '.stat.total .num { color: #667eea; }',
              'h2 { font-size: 18px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px solid #f0f0f0; color: #444; }',
              'table { width: 100%; border-collapse: collapse; }',
              'th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid #eee; }',
              'th { background: #f8f9fa; font-weight: 600; color: #555; font-size: 13px; }',
              'tr:hover { background: #f8f9fa; }',
              'ul { padding-left: 20px; }',
              'li { padding: 4px 0; }',
              'code { background: #f4f4f4; padding: 2px 6px; border-radius: 4px; font-size: 13px; }',
              '.footer { text-align: center; font-size: 12px; color: #aaa; padding: 20px; }',
              '</style>', '</head>', '<body>', '<div class="container">',
              f'<div class="header">',
              f'<div class="op">{report["operation"].upper()} Report</div>',
              f'<h1>开发环境配置报告</h1>',
              f'<div style="font-size:13px;opacity:0.7">{report["timestamp"]}</div>',
              f'<div class="status-badge">{s["status"]}</div>',
              '</div>',
              f'<div class="stats">',
              f'<div class="stat total"><div class="num">{s["total_requested"]}</div><div class="label">请求总数</div></div>',
              f'<div class="stat success"><div class="num">{s["success"]}</div><div class="label">成功</div></div>',
              f'<div class="stat failed"><div class="num">{s["failed"]}</div><div class="label">失败</div></div>',
              f'<div class="stat skipped"><div class="num">{s["skipped"]}</div><div class="label">跳过</div></div>',
              '</div>',
              ]

    # Env status table
    if env_rows:
        parts.append('<div class="card section"><h2>Environment Status</h2>')
        parts.append('<table><thead><tr><th></th><th>Result</th><th>Environment</th></tr></thead><tbody>')
        parts.append(env_rows)
        parts.append('</tbody></table></div>')

    # Completed
    if completed_rows:
        parts.append('<div class="card section"><h2>Completed')
        parts.append(f' ({len(d["completed"])})')
        parts.append('</h2><table><thead><tr><th></th><th>Environment</th><th>Status</th></tr></thead><tbody>')
        parts.append(completed_rows)
        parts.append('</tbody></table></div>')

    # Failed
    if failed_rows:
        parts.append('<div class="card section"><h2>Failed')
        parts.append(f' ({len(d["failed"])})')
        parts.append('</h2><table><thead><tr><th></th><th>Environment</th><th>Reason</th></tr></thead><tbody>')
        parts.append(failed_rows)
        parts.append('</tbody></table></div>')

    # Skipped
    if skipped_rows:
        parts.append('<div class="card section"><h2>Skipped')
        parts.append(f' ({len(d["skipped"])})')
        parts.append('</h2><table><thead><tr><th></th><th>Environment</th><th>Reason</th></tr></thead><tbody>')
        parts.append(skipped_rows)
        parts.append('</tbody></table></div>')

    # Env vars
    if envvar_rows:
        parts.append('<div class="card section"><h2>Environment Variables Changed')
        parts.append(f' ({len(d["env_vars_changed"])})')
        parts.append('</h2><table><thead><tr><th>Source</th><th>Variable</th><th>Value</th></tr></thead><tbody>')
        parts.append(envvar_rows)
        parts.append('</tbody></table></div>')

    # Network
    if network_items:
        parts.append('<div class="card section"><h2>Network Sources Used</h2><ul>')
        parts.append(network_items)
        parts.append('</ul></div>')

    # Next steps
    if steps_items:
        parts.append('<div class="card section"><h2>Next Steps</h2><ul>')
        parts.append(steps_items)
        parts.append('</ul></div>')

    parts.append(f'<div class="footer">Generated by dev-environment-setup skill &bull; {report["timestamp"]}</div>')
    parts.append('</div></body></html>')

    return '\n'.join(parts)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate environment setup report")
    parser.add_argument("--operation", required=True, choices=["install", "uninstall"], help="Operation type")
    parser.add_argument("--selected", nargs="+", help="Originally selected environments")
    parser.add_argument("--completed", nargs="+", default=[], help="Successfully completed environments")
    parser.add_argument("--failed", nargs="+", default=[], help="Failed environments (names only)")
    parser.add_argument("--failed-reasons", nargs="*", default=[], help="Reasons for failures (name:reason pairs)")
    parser.add_argument("--skipped", nargs="+", default=[], help="Skipped environments")
    parser.add_argument("--skipped-reasons", nargs="*", default=[], help="Reasons for skips")
    parser.add_argument("--env-status", default=None, help="JSON file with env status")
    parser.add_argument("--env-vars", default=None, help="JSON file with env var changes")
    parser.add_argument("--network", nargs="+", default=[], help="Network sources used")
    parser.add_argument("--base-dir", default="")
    parser.add_argument("--system-drive", default="C:\\")
    parser.add_argument("--output-dir", default=None, help="Report output directory")
    parser.add_argument("--json", action="store_true", help="Output as JSON only (no print)")
    args = parser.parse_args()

    # Load env status
    env_status = {}
    if args.env_status and os.path.isfile(args.env_status):
        with open(args.env_status, "r") as f:
            env_status = json.load(f)

    # Load env vars
    env_vars_changed = []
    if args.env_vars and os.path.isfile(args.env_vars):
        with open(args.env_vars, "r") as f:
            env_vars_changed = json.load(f)

    # Build failed details
    failed_details = []
    if args.failed:
        reasons_map = {}
        for pair in args.failed_reasons:
            if ":" in pair:
                name, reason = pair.split(":", 1)
                reasons_map[name.strip()] = reason.strip()
        for name in args.failed:
            failed_details.append({"name": name, "reason": reasons_map.get(name, "unknown")})

    # Build skipped details
    skipped_details = []
    if args.skipped:
        reasons_map = {}
        for pair in args.skipped_reasons:
            if ":" in pair:
                name, reason = pair.split(":", 1)
                reasons_map[name.strip()] = reason.strip()
        for name in args.skipped:
            skipped_details.append({"name": name, "reason": reasons_map.get(name, "")})

    report = generate_report(
        operation=args.operation,
        selected_envs=args.selected or [],
        completed_envs=args.completed or [],
        failed_envs=failed_details,
        skipped_envs=skipped_details,
        env_status=env_status,
        env_vars_changed=env_vars_changed,
        network_used=args.network or [],
        base_dir=args.base_dir,
        system_drive=args.system_drive,
    )

    # Save report
    report_path = save_report(report, args.output_dir)
    print(f"  Report saved: {report_path}")

    if args.json:
        import json as _json
        print(_json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_report(report)


if __name__ == "__main__":
    main()
