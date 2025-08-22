import os, re, requests, textwrap

USERNAME = os.getenv("GH_USERNAME", "APonder-Dev")
TOKEN = os.getenv("GITHUB_TOKEN")

API = "https://api.github.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

README_PATH = "README.md"

def fetch_recent_events(username: str, limit: int = 5):
    # GitHub Events API (public events)
    # We'll show PushEvent/IssuesEvent/PullRequestEvent
    r = requests.get(f"{API}/users/{username}/events/public", headers=HEADERS, timeout=20)
    r.raise_for_status()
    events = []
    for e in r.json():
        et = e.get("type")
        repo = e.get("repo", {}).get("name", "")
        if et == "PushEvent":
            commits = e.get("payload", {}).get("commits", [])
            if commits:
                msg = commits[-1].get("message", "")[:120]
                events.append(f"🔨 Pushed to **{repo}** — _{msg}_")
        elif et == "PullRequestEvent":
            pr = e.get("payload", {}).get("pull_request", {})
            action = e.get("payload", {}).get("action", "updated")
            title = pr.get("title", "(no title)")[:120]
            events.append(f"🔁 {action.title()} PR in **{repo}** — _{title}_")
        elif et == "IssuesEvent":
            issue = e.get("payload", {}).get("issue", {})
            action = e.get("payload", {}).get("action", "updated")
            title = issue.get("title", "(no title)")[:120]
            events.append(f"❗ {action.title()} issue in **{repo}** — _{title}_")
        if len(events) >= limit:
            break
    return events

def fetch_pinned_repos(username: str, limit: int = 4):
    # No official API for "pinned", so we’ll fallback to top public repos by stars.
    # (Alternatively: use a manual allowlist below.)
    r = requests.get(f"{API}/users/{username}/repos?per_page=100&sort=updated", headers=HEADERS, timeout=20)
    r.raise_for_status()
    repos = sorted(r.json(), key=lambda x: (x.get("stargazers_count", 0), x.get("forks_count", 0)), reverse=True)
    out = []
    for repo in repos:
        if repo.get("fork"):
            continue
        name = repo["name"]
        desc = (repo.get("description") or "").strip()
        stars = repo.get("stargazers_count", 0)
        url = repo.get("html_url")
        line = f"- [{name}]({url}) — {desc} ⭐{stars}"
        out.append(line)
        if len(out) >= limit:
            break
    return out

def make_stats_cards(username: str):
    # Use popular third-party stat images (no code changes, just image embeds)
    # If you prefer not to rely on external services, remove this section.
    return textwrap.dedent(f"""
    <p>
      <img src="https://github-readme-stats.vercel.app/api?username={username}&show_icons=true&hide_title=true" height="140" />
      <img src="https://github-readme-stats.vercel.app/api/top-langs/?username={username}&layout=compact" height="140" />
    </p>
    """).strip()

def replace_section(content: str, marker: str, new_block: str) -> str:
    pattern = re.compile(
        rf"(<!--{marker}:START-->)(.*?)(<!--{marker}:END-->)",
        re.DOTALL
    )
    repl = rf"\1\n{new_block}\n\3"
    if not pattern.search(content):
        # If markers missing, append at end
        return content + f"\n\n<!--{marker}:START-->\n{new_block}\n<!--{marker}:END-->\n"
    return pattern.sub(repl, content)

def main():
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme = f.read()

    # Recent activity
    recent = fetch_recent_events(USERNAME, limit=6)
    recent_md = "\n".join(f"- {line}" for line in (recent or ["(no recent public activity)"]))
    readme = replace_section(readme, "RECENT_ACTIVITY", recent_md)

    # Stats cards
    stats_md = make_stats_cards(USERNAME)
    readme = replace_section(readme, "STATS", stats_md)

    # Pinned repos (heuristic)
    pinned = fetch_pinned_repos(USERNAME, limit=4)
    pinned_md = "\n".join(pinned or ["(pin a few repos to showcase your best work)"])
    readme = replace_section(readme, "PINNED", pinned_md)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(readme)

if __name__ == "__main__":
    main()
