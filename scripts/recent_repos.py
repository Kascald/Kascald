import json, os, re, sys, time, urllib.request
from datetime import datetime, timezone

USER = os.environ["GH_USER"]
COUNT = int(os.environ.get("REPO_COUNT", "5"))
STALE_DAYS = int(os.environ.get("STALE_DAYS", "50"))
LAST_COMMIT = int(os.environ["LAST_COMMIT_TS"])
README = "README.md"
START, END = "<!-- RECENT:START -->", "<!-- RECENT:END -->"

req = urllib.request.Request(
    f"https://api.github.com/users/{USER}/repos?type=owner&sort=pushed&per_page=100",
    headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
             "Accept": "application/vnd.github+json"},
)
repos = json.load(urllib.request.urlopen(req))
repos = [r for r in repos
         if not r["fork"] and not r["archived"] and not r["private"]
         and r["name"].lower() != USER.lower()][:COUNT]

lines = []
for r in repos:
    meta = " · ".join(x for x in (r["language"], r["description"]) if x)
    lines.append(f"- [**{r['name']}**]({r['html_url']})" + (f" — {meta}" if meta else ""))
listing = "\n".join(lines)

text = open(README, encoding="utf-8").read()
m = re.search(re.escape(START) + r"\n(.*?)" + re.escape(END), text, re.S)
if not m:
    sys.exit("markers not found")
old_listing = re.sub(r"\n*<sub>Updated .*?</sub>\n?", "", m.group(1)).strip()

stale = time.time() - LAST_COMMIT >= STALE_DAYS * 86400
if listing == old_listing and not stale:
    print("no change")
    sys.exit(0)

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
block = f"{START}\n{listing}\n\n<sub>Updated {today}</sub>\n{END}"
open(README, "w", encoding="utf-8").write(text[:m.start()] + block + text[m.end():])
print("updated" + (" (stale refresh)" if listing == old_listing else ""))
