"""Phase 1a - collect today's trending items from free, keyless sources.

Every source is wrapped so that one failing source never kills the run
(Reddit in particular often blocks datacenter IPs such as GitHub runners).
"""
import xml.etree.ElementTree as ET
import requests

UA = {"User-Agent": "yt-autopilot/0.1 (personal research bot)"}
TIMEOUT = 20


def hacker_news(limit=15):
    base = "https://hacker-news.firebaseio.com/v0"
    ids = requests.get(f"{base}/topstories.json", timeout=TIMEOUT).json()[:limit]
    out = []
    for i in ids:
        d = requests.get(f"{base}/item/{i}.json", timeout=TIMEOUT).json()
        if d and d.get("title"):
            out.append({"source": "hackernews", "title": d["title"],
                        "score": d.get("score", 0), "url": d.get("url", "")})
    return out


def google_trends(geo="US", limit=15):
    r = requests.get(f"https://trends.google.com/trending/rss?geo={geo}",
                     headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = []
    for item in root.iter("item"):
        row = {"source": f"google_trends_{geo}", "title": "", "traffic": ""}
        for child in item:
            tag = child.tag.split("}")[-1]
            if tag == "title":
                row["title"] = (child.text or "").strip()
            elif tag == "approx_traffic":
                row["traffic"] = (child.text or "").strip()
        if row["title"]:
            out.append(row)
        if len(out) >= limit:
            break
    return out


def reddit(subs, limit=10):
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out = []
    errors = []
    for sub in subs:
        try:
            r = requests.get(f"https://www.reddit.com/r/{sub}/top/.rss?t=day",
                             headers=UA, timeout=TIMEOUT)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for e in root.findall("a:entry", ns)[:limit]:
                t = e.find("a:title", ns)
                if t is not None and t.text:
                    out.append({"source": f"r/{sub}", "title": t.text.strip()})
        except Exception as ex:
            errors.append(f"r/{sub}: {ex}")
    if not out and errors:
        raise RuntimeError("; ".join(errors))
    return out


def collect(cfg):
    items, errors = [], []
    jobs = [
        ("hackernews", lambda: hacker_news(cfg["hn_limit"])),
        ("google_trends", lambda: google_trends(cfg["google_trends_geo"], cfg["trends_limit"])),
        ("reddit", lambda: reddit(cfg["reddit_subs"], cfg["reddit_limit"])),
    ]
    for name, fn in jobs:
        try:
            items += fn()
        except Exception as ex:  # keep going, report at the end
            errors.append(f"{name}: {ex}")
    return items, errors
