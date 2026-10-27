"""Draw a Tokyo Night GitHub stats card, private contributions included.

Usage: python stats.py <github-user> <out.svg>   (needs GITHUB_TOKEN in env;
a PAT of the user itself is what makes private repos count)
"""
import os
import sys
from html import escape

from activity import ACCENT, AXIS, BG, FONT, MONO, MUTED, POINT, graphql

W, H = 450, 195
TEXT = "#d5deff"


def fetch_stats(user: str, token: str) -> dict:
    query = """query($login:String!){user(login:$login){
      contributionsCollection{
        contributionYears totalCommitContributions restrictedContributionsCount
        contributionCalendar{totalContributions}}
      pullRequests{totalCount}
      issues{totalCount}
      repositories(ownerAffiliations:OWNER, isFork:false, first:100){
        totalCount nodes{stargazerCount}}}}"""
    u = graphql(query, {"login": user}, token)["user"]
    cc = u["contributionsCollection"]

    # one aliased collection per year, since a collection spans at most a year
    years = cc["contributionYears"]
    parts = " ".join(
        f'y{y}:contributionsCollection(from:"{y}-01-01T00:00:00Z",to:"{y}-12-31T23:59:59Z")'
        "{contributionCalendar{totalContributions}}"
        for y in years
    )
    per_year = graphql(f"query($login:String!){{user(login:$login){{{parts}}}}}", {"login": user}, token)["user"]

    return {
        "all_time": sum(v["contributionCalendar"]["totalContributions"] for v in per_year.values()),
        "last_year": cc["contributionCalendar"]["totalContributions"],
        # with the owner's token private commits are already in the first number;
        # otherwise they only show up as anonymous restricted contributions
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "since": min(years) if years else None,
    }


def render(s: dict, title: str) -> str:
    rows = [
        ("Contributions (last year)", s["last_year"]),
        ("Commits (last year)", s["commits"]),
        ("Pull requests", s["prs"]),
        ("Issues", s["issues"]),
        ("Repositories", s["repos"]),
        ("Stars earned", s["stars"]),
    ]
    title = escape(title)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}">',
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>',
        f'<text x="24" y="36" font-family="{FONT}" font-size="17" font-weight="600" fill="{ACCENT}">{title}</text>',
    ]
    for i, (label, value) in enumerate(rows):
        y = 66 + i * 22
        out.append(f'<circle cx="28" cy="{y - 4}" r="3" fill="{POINT}"/>')
        out.append(f'<text x="40" y="{y}" font-family="{FONT}" font-size="13" fill="{TEXT}">{label}</text>')
        out.append(f'<text x="270" y="{y}" text-anchor="end" font-family="{MONO}" font-size="13" font-weight="700" fill="{TEXT}">{value:,}</text>')

    cx, cy = 362, 106
    out.append(f'<circle cx="{cx}" cy="{cy}" r="52" fill="none" stroke="{AXIS}" stroke-width="6"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="52" fill="none" stroke="{ACCENT}" stroke-width="6" stroke-opacity="0.85"/>')
    out.append(f'<text x="{cx}" y="{cy + 2}" text-anchor="middle" font-family="{FONT}" font-size="24" font-weight="700" fill="{ACCENT}">{s["all_time"]:,}</text>')
    out.append(f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{MUTED}">all-time</text>')
    if s["since"]:
        out.append(f'<text x="{cx}" y="{cy + 74}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{MUTED}">contributions since {s["since"]}</text>')
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    user, path = sys.argv[1], sys.argv[2]
    stats = fetch_stats(user, os.environ["GITHUB_TOKEN"])
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render(stats, "Bao Tran's GitHub stats"))
