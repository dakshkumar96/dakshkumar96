"""
Generates assets/radar-langs-dark.svg and assets/radar-langs-light.svg —
the "what I actually ship" side of the skill-radar pair, reusing the
drawing code from radar.py. Same 6 axes as skills.json's self-rated side
(Python, SQL/Data, TypeScript/JS, PyTorch/ML, RAG/LLMs, Docker/Deploy),
each computed a different but equally real way:

- Python / SQL/Data / TypeScript/JS: share of real bytes across all
  non-fork repos (language_bytes(), same source the languages section
  elsewhere in this README uses).
- PyTorch/ML / RAG/LLMs: fraction of non-fork repos whose dependency
  manifest (requirements.txt / pyproject.toml / package.json) actually
  names a matching library — not GitHub's code-search index, which
  tested unreliable for this (returned 0 hits for a Dockerfile
  confirmed to exist), but a direct fetch-and-grep of each repo's own
  tree via the Contents API.
- Docker/Deploy: fraction of non-fork repos with a Dockerfile anywhere
  in their tree.

Deliberately not the same kind of number as the self-rated chart —
these are independently verifiable facts about the repos, not a second
set of guesses dressed up as measurement. GitHub doesn't expose "how
much of your PyTorch confidence is real" any more directly than this.
"""
import base64

import svgkit
from gh_api import all_repos, language_bytes, rest_get
from radar import draw, RADIUS

BLUE = "#3B82F6"  # this chart's own accent — see radar.draw()'s color param

ML_KEYWORDS = ["torch", "pytorch", "tensorflow", "scikit-learn", "sklearn"]
LLM_KEYWORDS = [
    "langchain", "faiss", "sentence-transformers", "sentence_transformers",
    "openai", "anthropic", "google-generativeai", "gemini", "@anthropic-ai",
]


def _repo_tree(owner, repo):
    try:
        return rest_get(f"/repos/{owner}/{repo}/git/trees/HEAD", {"recursive": 1}).get("tree", [])
    except Exception:
        return []


def _file_content(owner, repo, path):
    try:
        data = rest_get(f"/repos/{owner}/{repo}/contents/{path}")
        return base64.b64decode(data["content"]).decode("utf-8", errors="ignore").lower()
    except Exception:
        return ""


def compute_ship_metrics():
    repos = [r for r in all_repos() if not r["fork"]]
    total = len(repos) or 1

    docker_hits = ml_hits = llm_hits = 0

    for repo in repos:
        owner, name = repo["owner"]["login"], repo["name"]
        paths = [t["path"] for t in _repo_tree(owner, name)]

        if any(p.rsplit("/", 1)[-1] == "Dockerfile" for p in paths):
            docker_hits += 1

        manifest_paths = [
            p for p in paths
            if p.rsplit("/", 1)[-1] in ("requirements.txt", "pyproject.toml", "package.json")
        ]
        combined = " ".join(_file_content(owner, name, p) for p in manifest_paths)
        if any(k in combined for k in ML_KEYWORDS):
            ml_hits += 1
        if any(k in combined for k in LLM_KEYWORDS):
            llm_hits += 1

    langs = language_bytes()
    total_bytes = sum(langs.values()) or 1
    python_pct = langs.get("Python", 0) / total_bytes * 100
    sql_pct = (langs.get("SQL", 0) + langs.get("PLpgSQL", 0)) / total_bytes * 100
    ts_js_pct = (langs.get("TypeScript", 0) + langs.get("JavaScript", 0)) / total_bytes * 100

    return {
        "Python": python_pct,
        "SQL / Data": sql_pct,
        "TypeScript / JS": ts_js_pct,
        "PyTorch / ML": ml_hits / total * 100,
        "RAG / LLMs": llm_hits / total * 100,
        "Docker / Deploy": docker_hits / total * 100,
    }


def build(p):
    metrics = compute_ship_metrics()
    w, h = 572, 418  # same canvas as radar.py's build() — matched pair
    svg = [svgkit.svg_open(w, h, p), svgkit.panel(11, 11, w - 22, h - 22, p)]
    svg.append(draw(
        w / 2, h / 2 + 7, RADIUS,
        list(metrics.keys()), list(metrics.values()), p,
        value_labels=list(metrics.values()), color=BLUE,
    ))
    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    svgkit.render_pair(build, "assets/radar-langs-dark.svg", "assets/radar-langs-light.svg")
