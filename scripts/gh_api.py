"""
Minimal GitHub REST + GraphQL client shared by every script in scripts/.

Auth: uses GH_TOKEN if set, falling back to GITHUB_TOKEN (the automatic
token GitHub Actions injects into every workflow run). Both are enough to
read public profile/contribution data for TARGET_USER.
"""
import datetime as dt
import json
import os
import time
import requests

TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
USER = os.environ.get("TARGET_USER", "dakshkumar96")

REST = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"


def _headers():
    h = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def rest_get(path, params=None):
    r = requests.get(f"{REST}{path}", headers=_headers(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def graphql(query, variables=None):
    r = requests.post(
        GRAPHQL,
        headers=_headers(),
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def profile(user=None):
    return rest_get(f"/users/{user or USER}")


def all_repos(user=None):
    """Every owned repo (paginated), not just the first page."""
    user = user or USER
    repos, page = [], 1
    while True:
        batch = rest_get(f"/users/{user}/repos", {"per_page": 100, "page": page, "type": "owner"})
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def language_bytes(user=None):
    """Aggregate language byte-counts across all non-fork repos."""
    totals = {}
    for repo in all_repos(user):
        if repo.get("fork"):
            continue
        langs = rest_get(f"/repos/{repo['owner']['login']}/{repo['name']}/languages")
        for lang, n in langs.items():
            totals[lang] = totals.get(lang, 0) + n
    return totals


def profile_views(user=None):
    """
    Current count from the komarev.com hit-counter badge already embedded
    in the README. This is a real read of the live counter (parsed from
    its own rendered <title>), not a fabricated number — but two honest
    caveats: fetching the badge is itself a hit, so each scheduled run of
    this pipeline adds one to the count same as any real page view would;
    and GitHub's camo image proxy caches the badge for a stretch of time,
    so many real visitors within that window share a single underlying
    fetch. Both are inherent to this class of badge service, not
    something introduced here.
    """
    import re

    user = user or USER
    # must match the exact query string embedded in the README — komarev
    # renders a visually different (and differently-labelled) badge
    # depending on color/label/style, so a mismatched URL parses as 0
    r = requests.get(
        f"https://komarev.com/ghpvc/?username={user}&color=3B82F6&label=profile+views&style=for-the-badge",
        timeout=15,
    )
    r.raise_for_status()
    m = re.search(r'aria-label="[^:"]*:\s*(\d+)"', r.text)
    return int(m.group(1)) if m else 0


_COMMITS_CACHE = os.path.join(".cache", "public_commits.json")
# deliberately NOT under dist/ — the snake-animation Docker action (Platane/snk)
# creates dist/ as root inside its container, and the runner user can't write
# into it afterward; this caused a real PermissionError in CI


def _search_commits_page(user, page, retries=3):
    """The Search API has its own, much stricter rate limit than core REST
    (tens of requests/minute). A 403 there is almost always that limit, not
    an auth problem — worth a short backoff-and-retry rather than failing
    the whole generation run over a transient limit."""
    for attempt in range(retries):
        try:
            return rest_get(
                "/search/commits",
                {"q": f"author:{user}", "sort": "author-date", "order": "asc", "per_page": 100, "page": page},
            )
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 403 and attempt < retries - 1:
                time.sleep(15 * (attempt + 1))
                continue
            raise


def public_commits(user=None):
    """
    Every public commit authored by `user`, across every public repo on
    GitHub (not just ones they own) — via the Search Commits API, which
    only ever indexes public content, so this is guaranteed public-only
    regardless of what the calling token can otherwise see.

    Returns a list of author-date datetimes, sorted ascending. This is the
    single source of truth for total-commit-count, active-day-count, and
    the commit-activity chart, so those three numbers can never disagree
    with each other — and it's cached to dist/ for the run, since both
    commit_line.py and card_stats.py need it and the Search API's rate
    limit is tight enough that fetching it twice in one run risks a 403.

    Capped at the Search API's 1000-result ceiling; fine at current scale,
    but note it here rather than silently truncating without a trace.
    """
    user = user or USER

    if os.path.exists(_COMMITS_CACHE):
        with open(_COMMITS_CACHE, encoding="utf-8") as f:
            cached = json.load(f)
        if cached.get("user") == user:
            return [dt.datetime.fromisoformat(s) for s in cached["dates"]]

    dates = []
    page = 1
    while True:
        data = _search_commits_page(user, page)
        items = data.get("items", [])
        if not items:
            break
        for item in items:
            # author dates carry whatever timezone offset the committer's
            # machine was in (not always "Z"/UTC) — parse it as given, then
            # normalize to naive UTC so every date in the list compares
            # consistently regardless of where it was authored
            raw = item["commit"]["author"]["date"].replace("Z", "+00:00")
            parsed = dt.datetime.fromisoformat(raw)
            dates.append(parsed.astimezone(dt.timezone.utc).replace(tzinfo=None))
        if len(dates) >= data["total_count"] or len(items) < 100 or page * 100 >= 1000:
            break
        page += 1
        time.sleep(1.5)  # pace the pages — see _search_commits_page

    os.makedirs(os.path.dirname(_COMMITS_CACHE), exist_ok=True)
    with open(_COMMITS_CACHE, "w", encoding="utf-8") as f:
        json.dump({"user": user, "dates": [d.isoformat() for d in dates]}, f)
    return dates


CONTRIB_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""


def contributions(frm, to, login=None):
    """GraphQL contribution calendar for one date window (max ~1 year span)."""
    return graphql(CONTRIB_QUERY, {"login": login or USER, "from": frm, "to": to})["user"][
        "contributionsCollection"
    ]
