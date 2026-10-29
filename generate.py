#!/usr/bin/env python3
"""Builds terminal.svg and terminal-mobile.svg for the GitHub profile README.

Stats come from the public GitHub API (no invented numbers). If the API cannot be
reached, stat values show "--". Usage:
  USERNAME=your-username [GITHUB_TOKEN=...] python3 generate.py
"""
import json, os, sys, urllib.request, urllib.parse
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
USERNAME = os.environ.get("USERNAME") or os.environ.get("GITHUB_REPOSITORY_OWNER") or ""
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ---- edit your details here -------------------------------------------------
HEADER = "nj@github"
SECTIONS = [
    ("System", [
        ("Role:", ["Software Developer"], None),
        ("Location:", ["Philippines"], None),
        ("Education:", ["BS Computer Engineering"], None),
    ]),
    ("Stack", [
        ("Languages:", ["PHP, JavaScript, SQL, Dart"], None),
        ("Frameworks:", ["CodeIgniter 4, Flutter"], None),
        ("Tools:", ["Git, GitHub, Sourcetree, MySQL, VS Code, Laragon"], None),
    ]),
    ("Focus", [
        ("Interests:", ["Backend development, database design,",
                        "application security, automation, system architecture"], None),
        ("Hobbies:", ["Motorcycles, gaming"], None),
    ]),
    ("Contact", [
        ("Portfolio:", ["neiljoshua.netlify.app"], "link"),
    ]),
]
# -----------------------------------------------------------------------------

C = dict(bg="#0d1117", bd="#30363d", head="#58a6ff", lab="#e3b341", sep="#6e7681",
         txt="#c9d1d9", art="#adbac7", link="#58a6ff")
FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"

def api(path):
    req = urllib.request.Request("https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme-generator"})
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def graphql_commits(login, created_at):
    """Total commit contributions across all years (includes private ones if the
    profile setting 'Include private contributions' is on)."""
    import datetime as dt
    q = ("query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){"
         "contributionsCollection(from:$from,to:$to){totalCommitContributions restrictedContributionsCount}}}")
    now = dt.datetime.now(dt.timezone.utc)
    total = 0
    for year in range(int(created_at[:4]), now.year + 1):
        start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
        end = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
        body = json.dumps({"query": q, "variables": {"login": login,
            "from": start.strftime("%Y-%m-%dT%H:%M:%SZ"), "to": end.strftime("%Y-%m-%dT%H:%M:%SZ")}}).encode()
        req = urllib.request.Request("https://api.github.com/graphql", data=body, method="POST",
            headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json",
                     "User-Agent": "profile-readme-generator"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        if "errors" in data:
            raise RuntimeError(data["errors"][0].get("message", "graphql error"))
        c = data["data"]["user"]["contributionsCollection"]
        total += c["totalCommitContributions"] + c["restrictedContributionsCount"]
    return total

def fetch_stats():
    na = "--"
    s = {"Repos:": na, "Stars:": na, "Commits:": na, "Followers:": na}
    if not USERNAME:
        print("USERNAME not set: stats left as '--'", file=sys.stderr); return s
    u = urllib.parse.quote(USERNAME)
    user = {}
    try:
        user = api(f"/users/{u}")
        s["Repos:"] = f'{user["public_repos"]:,}'
        s["Followers:"] = f'{user["followers"]:,}'
    except Exception as e: print("user:", e, file=sys.stderr)
    try:
        stars, page = 0, 1
        while page <= 10:
            repos = api(f"/users/{u}/repos?per_page=100&page={page}")
            stars += sum(r["stargazers_count"] for r in repos if not r["fork"])
            if len(repos) < 100: break
            page += 1
        s["Stars:"] = f"{stars:,}"
    except Exception as e: print("stars:", e, file=sys.stderr)
    commits = None
    if TOKEN:
        try:
            commits = graphql_commits(USERNAME, user.get("created_at", "2008-01-01T00:00:00Z"))
        except Exception as e: print("graphql commits:", e, file=sys.stderr)
    if commits is None:
        try:
            commits = api(f"/search/commits?q=author:{u}&per_page=1")["total_count"]
        except Exception as e: print("search commits:", e, file=sys.stderr)
    if commits is not None:
        s["Commits:"] = f"{commits:,}"
    return s

def build(rows, art, W, fs, lh, x_info, x_end, charw, show_art):
    out, y = [], 0
    def add(s): out.append(s)
    add(f'<circle cx="24" cy="22" r="6" fill="#f85149"/><circle cx="44" cy="22" r="6" fill="#e3b341"/><circle cx="64" cy="22" r="6" fill="#3fb950"/>')
    add(f'<line x1="0.5" y1="44" x2="{W-0.5}" y2="44" stroke="{C["bd"]}"/>')
    y0 = 78
    y = y0
    # header
    hw = len(HEADER) * charw
    add(f'<text x="{x_info}" y="{y}" font-size="{fs}" class="head">{escape(HEADER)}</text>')
    add(f'<line x1="{x_info+hw+8:.0f}" y1="{y-4}" x2="{x_end}" y2="{y-4}" stroke="{C["sep"]}" stroke-width="1"/>')
    y += lh
    for title, items in rows:
        y += lh * 0.55
        tw = (len(title) + 2) * charw
        add(f'<text x="{x_info}" y="{y}" font-size="{fs}" class="head">&#8212; {escape(title)}</text>')
        add(f'<line x1="{x_info+tw+6:.0f}" y1="{y-4}" x2="{x_end}" y2="{y-4}" stroke="{C["sep"]}" stroke-width="1"/>')
        y += lh * 1.15
        for label, vals, kind in items:
            for j, v in enumerate(vals):
                cls = "link" if kind == "link" else "txt"
                if j == 0:
                    add(f'<text x="{x_info}" y="{y}" font-size="{fs}" class="lab">{escape(label)}</text>')
                    x1 = x_info + len(label) * charw + 8
                    x2 = x_end - len(v) * charw - 8
                    if x2 - x1 > 12:
                        add(f'<line x1="{x1:.0f}" y1="{y-3}" x2="{x2:.0f}" y2="{y-3}" stroke="{C["sep"]}" stroke-width="1.5" stroke-dasharray="0.1 5" stroke-linecap="round"/>')
                add(f'<text x="{x_end}" y="{y}" font-size="{fs}" text-anchor="end" class="{cls}">{escape(v)}</text>')
                y += lh
    y_end = y
    H = max(y_end + 26, (y0 + len(art) * 10.4 + 40) if show_art else 0)
    if show_art:
        ay = (H - len(art) * 10.4) / 2 + 22
        for i, l in enumerate(art):
            add(f'<text x="26" y="{ay+i*10.4:.1f}" font-size="9" class="art" xml:space="preserve">{escape(l) or " "}</text>')
    style = (f'<style>text{{font-family:{FONT};white-space:pre}} .head{{fill:{C["head"]}}} .lab{{fill:{C["lab"]};font-weight:700}} '
             f'.txt{{fill:{C["txt"]}}} .link{{fill:{C["link"]}}} .art{{fill:{C["art"]}}}</style>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}" role="img" '
            f'aria-label="Terminal-style profile: Software Developer, Philippines">\n{style}\n'
            f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1:.0f}" rx="10" fill="{C["bg"]}" stroke="{C["bd"]}"/>\n'
            + "\n".join(out) + "\n</svg>\n")

def main():
    art = open(os.path.join(HERE, "art.txt")).read().rstrip("\n").split("\n")
    stats = fetch_stats()
    rows = SECTIONS + [("GitHub Stats", [(k, [v], None) for k, v in stats.items()])]
    open(os.path.join(HERE, "terminal.svg"), "w").write(build(rows, art, 980, 13, 20, 380, 944, 7.9, True))
    open(os.path.join(HERE, "terminal-mobile.svg"), "w").write(build(rows, art, 470, 12, 19, 24, 446, 7.3, False))
    print("wrote terminal.svg and terminal-mobile.svg", stats)

if __name__ == "__main__":
    main()
