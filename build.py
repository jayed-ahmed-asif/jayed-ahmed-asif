#!/usr/bin/env python3
"""Rebuilds assets/spectrum.svg and the generated sections of README.md
from the JSON files in config/. No third-party packages needed."""
import json, math, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

# ---------- Spectrum SVG ----------
def build_spectrum(cfg):
    W, H = cfg["width"], cfg["height"]
    BASE = H - 65
    bands = cfg["bands"]
    n, bw, gap, ggap = cfg["bars_per_band"], cfg["bar_width"], cfg["bar_gap"], cfg["band_gap"]
    gw = n * (bw + gap) - gap
    total = len(bands) * gw + (len(bands) - 1) * ggap
    x0 = (W - total) / 2
    max_h = BASE - 20
    rnd = random.Random(cfg["seed"])

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Animated spectrum analyzer">', "<defs>"]
    for i, b in enumerate(bands):
        o.append(f'<linearGradient id="g{i}" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="{b["color"]}"/><stop offset="1" stop-color="{b["light"]}"/></linearGradient>')
    o.append('<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0D1117"/><stop offset="1" stop-color="#111827"/></linearGradient>')
    o.append("</defs>")
    o.append(f'<rect width="{W}" height="{H}" rx="14" fill="url(#bg)" stroke="#2563EB" stroke-opacity="0.5"/>')
    for k in (0.25, 0.5, 0.75, 1.0):
        gy = BASE - int(max_h * k)
        o.append(f'<line x1="20" y1="{gy}" x2="{W-20}" y2="{gy}" stroke="#ffffff" stroke-opacity="0.05"/>')
    o.append(f'<line x1="20" y1="{BASE}" x2="{W-20}" y2="{BASE}" stroke="#ffffff" stroke-opacity="0.25"/>')

    for gi, b in enumerate(bands):
        gx = x0 + gi * (gw + ggap)
        for k in range(n):
            env = 0.45 + 0.55 * math.sin(math.pi * (k + 0.5) / n)
            vals = [max(12, int(rnd.uniform(0.25, 1.0) * max_h * 0.95 * env)) for _ in range(4)]
            vals.append(vals[0])
            hs = ";".join(map(str, vals))
            ys = ";".join(str(BASE - v) for v in vals)
            dur = round(rnd.uniform(cfg["speed_min"], cfg["speed_max"]), 2)
            x = gx + k * (bw + gap)
            o.append(
                f'<rect x="{x:.1f}" y="{BASE - vals[0]}" width="{bw}" height="{vals[0]}" rx="3" fill="url(#g{gi})">'
                f'<animate attributeName="height" values="{hs}" dur="{dur}s" repeatCount="indefinite"/>'
                f'<animate attributeName="y" values="{ys}" dur="{dur}s" repeatCount="indefinite"/></rect>')
        o.append(f'<text x="{gx + gw/2:.1f}" y="{BASE + 32}" text-anchor="middle" font-family="Courier New, monospace" font-size="15" font-weight="bold" fill="{b["color"]}">{b["name"]}</text>')
    o.append(f'<text x="{W/2}" y="{H - 11}" text-anchor="middle" font-family="Courier New, monospace" font-size="10" fill="#9CA3AF" letter-spacing="3">{cfg["title"]}</text>')
    o.append("</svg>")
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets" / "spectrum.svg").write_text("\n".join(o), encoding="utf-8")

def spectrum_table(cfg):
    rows = ["| BAND | FOCUS |", "|:---|:---|"]
    for b in cfg["bands"]:
        rows.append(f'| {b.get("emoji", "")} **{b["name"]}** | {b["focus"]} |')
    return "\n".join(rows)

# ---------- Achievements ----------
BADGES = {  # type: (label, color, logo)
    "certificate": ("VIEW-CERTIFICATE", "7C3AED", "googledrive"),
    "course":      ("VIEW-CERTIFICATE", "2563EB", "coursera"),
    "competition": ("VIEW-PROOF",       "00A6A6", "linkedin"),
    "project":     ("VIEW-LINK",        "FF6B9D", "github"),
    "other":       ("VIEW-LINK",        "181717", ""),
}

def esc(s):
    return str(s).replace("|", "\\|")

def achievements_table(cfg):
    rows = ["| 🏅 Achievement | 🏢 Issuer | 📅 Date | 🔗 Proof |", "|:---|:---|:---:|:---:|"]
    for a in cfg["achievements"]:
        label, color, logo = BADGES.get(a.get("type", "other"), BADGES["other"])
        link = a.get("link", "").strip()
        if link:
            logo_part = f"&logo={logo}&logoColor=white" if logo else ""
            proof = f"[![View](https://img.shields.io/badge/{label}-{color}?style=flat-square{logo_part})]({link})"
        else:
            proof = "—"
        rows.append(f'| {esc(a["title"])} | {esc(a.get("issuer", ""))} | {esc(a.get("date", ""))} | {proof} |')
    return "\n".join(rows)

# ---------- README injection ----------
def inject(text, name, content):
    pat = re.compile(rf"(<!-- {name}:START -->)(.*?)(<!-- {name}:END -->)", re.S)
    if not pat.search(text):
        raise SystemExit(f"Marker {name} not found in README.md")
    return pat.sub(lambda m: f"{m.group(1)}\n\n{content}\n\n{m.group(3)}", text)

def main():
    spec = load("config/spectrum.json")
    ach = load("config/achievements.json")
    build_spectrum(spec)
    readme_path = ROOT / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    text = inject(text, "SPECTRUM_TABLE", spectrum_table(spec))
    text = inject(text, "ACHIEVEMENTS", achievements_table(ach))
    readme_path.write_text(text, encoding="utf-8")
    print("Built assets/spectrum.svg and updated README.md")

if __name__ == "__main__":
    main()
