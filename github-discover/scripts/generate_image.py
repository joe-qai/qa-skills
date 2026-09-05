"""
Generate a visual card image for a GitHub repo (tech stack infographic).

Uses Pillow (PIL) only — no matplotlib dependency required.
Output: PNG image (~800x600) with repo name, stars, language, tech stack bars.

Usage:
    python generate_image.py \\
        --repo-meta <json> \\
        --analysis <json> \\
        --output <path.png>
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def load_json(arg: str) -> dict:
    if arg.startswith("{") or arg.startswith("["):
        return json.loads(arg)
    with open(arg, encoding="utf-8") as f:
        return json.load(f)


# Colors
BG_COLOR = (26, 26, 32)          # dark bg
ACCENT_COLOR = (99, 179, 237)    # blue accent
TEXT_COLOR = (235, 235, 245)     # light text
SUB_COLOR = (156, 163, 175)      # muted text
BAR_COLORS = [
    (99, 179, 237),   # blue
    (72, 187, 120),   # green
    (237, 137, 54),   # orange
    (237, 105, 149),  # pink
    (159, 122, 234),  # purple
]


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """Try common system fonts, fall back to default."""
    candidates = [
        ("C:\\Windows\\Fonts\\msyh.ttc", size),       # Microsoft YaHei
        ("C:\\Windows\\Fonts\\simhei.ttf", size),     # SimHei
        ("C:\\Windows\\Fonts\\ARIAL.TTF", size),      # Arial
    ]
    for path, sz in candidates:
        try:
            return ImageFont.truetype(path, sz)
        except Exception:
            continue
    return ImageFont.load_default()


def extract_deps(analysis: dict) -> list[str]:
    deps = []
    for dep_file in analysis.get("dependencies", []):
        for name in dep_file.get("dependencies", {}).keys():
            deps.append(name)
    return deps[:8]  # top 8


def draw_card(repo: dict, deps: list[str], output_path: str) -> None:
    W, H = 800, 520
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([(0, 0), (W, 6)], fill=ACCENT_COLOR)

    # Repo name (large)
    full_name = repo.get("full_name", "unknown/repo")
    font_title = get_font(36)
    bbox = draw.textbbox((0, 0), full_name, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, 40), full_name, fill=TEXT_COLOR, font=font_title)

    # Stars badge
    stars = repo.get("stargazers_count", 0)
    font_badge = get_font(22)
    stars_text = f"★ {stars:,}"
    bbox_s = draw.textbbox((0, 0), stars_text, font=font_badge)
    sw = bbox_s[2] - bbox_s[0]
    draw.rounded_rectangle(
        [(W // 2 - sw // 2 - 12, 90), (W // 2 + sw // 2 + 12, 126)],
        radius=6, fill=(45, 55, 72), outline=ACCENT_COLOR, width=1,
    )
    draw.text((W // 2 - sw // 2, 96), stars_text, fill=ACCENT_COLOR, font=font_badge)

    # Language badge
    lang = repo.get("language", "Unknown")
    font_lang = get_font(20)
    bbox_l = draw.textbbox((0, 0), lang, font=font_lang)
    lw = bbox_l[2] - bbox_l[0]
    draw.text(((W - lw) // 2, 140), lang, fill=SUB_COLOR, font=font_lang)

    # Description
    desc = repo.get("description", "")[:80]
    font_desc = get_font(18)
    bbox_d = draw.textbbox((0, 0), desc, font=font_desc)
    dw = bbox_d[2] - bbox_d[0]
    draw.text(((W - dw) // 2, 175), desc, fill=SUB_COLOR, font=font_desc)

    # Divider
    draw.rectangle([(80, 220), (W - 80, 222)], fill=(55, 65, 80))

    # Tech stack bars
    font_label = get_font(18)
    font_val = get_font(16)
    bar_y = 245
    max_bar_w = W - 200
    cols = len(deps)
    col_w = max_bar_w // max(cols, 1)

    for i, dep in enumerate(deps):
        color = BAR_COLORS[i % len(BAR_COLORS)]
        x = 80
        # Bar background
        draw.rounded_rectangle([(x, bar_y), (x + max_bar_w, bar_y + 28)], radius=4, fill=(45, 55, 72))
        # Bar fill (full width = shows it's a key dep)
        draw.rounded_rectangle([(x, bar_y), (x + max_bar_w, bar_y + 28)], radius=4, fill=color)
        # Label
        draw.text((x + 10, bar_y + 6), dep, fill=(255, 255, 255), font=font_label)
        bar_y += 38

    # Footer
    font_footer = get_font(14)
    footer_text = "github-discover  ·  今日热榜"
    bbox_f = draw.textbbox((0, 0), footer_text, font=font_footer)
    fw = bbox_f[2] - bbox_f[0]
    draw.text(((W - fw) // 2, H - 35), footer_text, fill=SUB_COLOR, font=font_footer)

    img.save(output_path, "PNG")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a tech stack card image for a GitHub repo")
    parser.add_argument("--repo-meta", required=True)
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--output", "-o", required=True)
    args = parser.parse_args()

    repo = load_json(args.repo_meta)
    analysis = load_json(args.analysis)
    deps = extract_deps(analysis)

    draw_card(repo, deps, args.output)


if __name__ == "__main__":
    main()
