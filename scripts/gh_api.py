"""
Minimal GitHub REST + GraphQL client shared by every script in scripts/.

Auth: uses GH_TOKEN if set, falling back to GITHUB_TOKEN (the automatic
token GitHub Actions injects into every workflow run). Both are enough to
read public profile/contribution data for TARGET_USER.
"""
import os
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
