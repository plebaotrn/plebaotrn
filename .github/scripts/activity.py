"""Draw a Tokyo Night area chart of the last 31 days of GitHub contributions.

Usage: python activity.py <github-user> <out.svg>   (needs GITHUB_TOKEN in env)
"""
import json
import os
import sys
import urllib.request

BG, GRID, AXIS = "#24283b", "#292e42", "#414868"
ACCENT, POINT, MUTED = "#bb9af7", "#7dcfff", "#a3b3e6"
W, H = 840, 260
LEFT, RIGHT, TOP, BOTTOM = 56, 24, 64, 44
FONT = "'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


def fetch_days(user: str, token: str):
    query = """query($login:String!){user(login:$login){contributionsCollection{
      contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    return [(d["date"], d["contributionCount"]) for d in days][-31:]


def nice_max(v: int) -> int:
    for step in (4, 8, 12, 16, 20, 40, 60, 80, 100, 200, 400, 1000):
        if v <= step:
            return step
    return v


def render(days, title: str) -> str:
    counts = [c for _, c in days]
    top = nice_max(max(counts + [1]))
    pw, ph = W - LEFT - RIGHT, H - TOP - BOTTOM
    xs = [LEFT + pw * i / (len(days) - 1) for i in range(len(days))]
    ys = [TOP + ph * (1 - c / top) for c in counts]
    line = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f} {y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    area = f"{line} L{xs[-1]:.1f} {TOP + ph} L{xs[0]:.1f} {TOP + ph} Z"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}">',
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>',
        f'<text x="24" y="38" font-family="{FONT}" font-size="17" font-weight="600" fill="{ACCENT}">{title}</text>',
        f'<text x="{W - 24}" y="38" text-anchor="end" font-family="{MONO}" font-size="12" fill="{MUTED}">last 31 days · {sum(counts)} contributions</text>',
    ]
    for k in range(5):
        v = top * k / 4
        y = TOP + ph * (1 - k / 4)
        out.append(f'<line x1="{LEFT}" y1="{y:.1f}" x2="{W - RIGHT}" y2="{y:.1f}" stroke="{AXIS if k == 0 else GRID}"/>')
        out.append(f'<text x="{LEFT - 10}" y="{y + 4:.1f}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">{int(v)}</text>')
    out.append(f'<path d="{area}" fill="{ACCENT}" fill-opacity="0.18"/>')
    out.append(f'<path d="{line}" fill="none" stroke="{ACCENT}" stroke-width="2.5" stroke-linejoin="round"/>')
    for x, y, c in zip(xs, ys, counts):
        if c == max(counts) and c > 0:
            out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{POINT}"/>')
    for i in (0, len(days) // 2, len(days) - 1):
        label = days[i][0][5:].replace("-", "/")
        anchor = "start" if i == 0 else "end" if i == len(days) - 1 else "middle"
        out.append(f'<text x="{xs[i]:.1f}" y="{H - 16}" text-anchor="{anchor}" font-family="{MONO}" font-size="11" fill="{MUTED}">{label}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    user, path = sys.argv[1], sys.argv[2]
    days = fetch_days(user, os.environ["GITHUB_TOKEN"])
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(days, "Bao Tran's contribution graph"))
