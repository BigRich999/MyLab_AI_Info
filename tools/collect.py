"""GeekNews 수집기 (GitHub Actions에서 매시간 실행).

- 클라우드 예약 작업은 news.hada.io에 접근할 수 없고, GeekNews는 봇 UA의 HTML 페이지 접근을 403으로 막습니다
  (2026-11-20 확인). RSS(Atom, 최근 20개)는 열리므로 RSS를 매시간 읽어 누적합니다.
- 글은 게시 시각 기준으로 발간 묶음에 넣습니다: (D-1 03:00, D 03:00] KST 에 게시된 글 → raw/D.json
- HTML 페이지는 봇 접근을 거르는 사이트 정책을 존중해 읽지 않습니다(RSS는 기계용으로 공개된 경로).

사용: python3 tools/collect.py
종료 코드: 0 정상, 2 RSS 실패
"""
import glob, html, json, os, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
BASE = "https://news.hada.io"
UA = "AI-Trend-Daily-RSS/1.0 (+https://github.com/BigRich999/MyLab_AI_Info)"  # 정직한 봇 UA. 브라우저 위장 금지
CUTOFF_H = 3  # 발간 묶음 경계(KST 03:00)
AI_KW = [
    "ai", "llm", "gpt", "openai", "anthropic", "claude", "gemini", "deepmind", "llama",
    "mistral", "deepseek", "qwen", "copilot", "cursor", "mcp", "agent", "agents", "agentic", "rag",
    "embedding", "transformer", "diffusion", "nvidia", "gpu", "tpu", "cuda", "hugging face", "inference",
    "prompt", "chatbot", "grok", "xai", "codex", "perplexity", "midjourney", "sora", "ml",
    "인공지능", "에이전트", "모델", "생성형", "머신러닝", "딥러닝", "학습", "추론", "챗봇",
    "프롬프트", "데이터센터", "반도체", "로봇", "자율주행", "벡터", "파인튜닝", "바이브", "토큰",
]


def fetch(url, log):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body, code = r.read().decode("utf-8", "replace"), r.status
    except urllib.error.HTTPError as e:
        body, code = "", e.code
    except Exception as e:
        log.append({"url": url, "status": "error", "detail": str(e)[:200]})
        return None
    ok = code == 200 and "cf-chl" not in body and "Just a moment" not in body
    log.append({"url": url, "status": "ok" if ok else "blocked", "http": code})
    time.sleep(1.0)
    return body if ok else None


def text(s):
    s = re.sub(r"<!\[CDATA\[([\s\S]*?)\]\]>", r"\1", s or "")
    if "&lt;" in s:
        s = html.unescape(s)
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", s, flags=re.I)
    s = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>|</ul>", "\n", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "\n- ", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t ]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


def tag(e, name):
    m = re.search(rf"<{name}\b[^>]*>([\s\S]*?)</{name}>", e)
    return m.group(1) if m else None


def bucket(dt):
    """게시 시각 → 발간일 D. (D-1 03:00, D 03:00] KST."""
    k = dt.astimezone(KST) - timedelta(hours=CUTOFF_H, microseconds=1)
    return (k.date() + timedelta(days=1)).isoformat()


def is_ai(it):
    s = f"{it.get('title') or ''} {(it.get('content') or '')[:400]}".lower()
    for k in AI_KW:
        if k.isascii():
            if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", s):
                return True
        elif k in s:
            return True
    return False


def parse_rss(body):
    out = []
    for e in re.findall(r"<entry>([\s\S]*?)</entry>", body):
        link = re.search(r"topic\?id=(\d+)", e)
        pub = tag(e, "published") or tag(e, "updated")
        if not link or not pub:
            continue
        try:
            dt = datetime.fromisoformat(pub.strip().replace("Z", "+00:00"))
        except ValueError:
            continue
        content = text(tag(e, "content") or tag(e, "summary") or "")
        orig = re.search(r"href=['\"]?(https?://(?!news\.hada\.io)[^'\" >]+)", html.unescape(tag(e, "content") or ""))
        out.append({
            "id": int(link.group(1)),
            "title": text(tag(e, "title")),
            "url": f"{BASE}/topic?id={link.group(1)}",
            "publishedAt": dt.astimezone(KST).isoformat(timespec="seconds"),
            "author": text(tag(e, "name") or ""),
            "originalUrl": orig.group(1) if orig else None,
            "content": content[:6000],
            "via": "rss",
            "_dt": dt,
        })
    return out


def main():
    now = datetime.now(KST)
    used = set()
    for f in glob.glob("data/20??-??-??.json"):
        used |= {it["id"] for it in json.load(open(f, encoding="utf-8"))["items"]}

    log = []
    body = fetch(f"{BASE}/rss/news", log)
    if not body:
        print(json.dumps({"status": "rss_failed", "log": log}, ensure_ascii=False))
        sys.exit(2)
    upd = tag(body, "updated")
    entries = parse_rss(body)

    # HTML 페이지는 봇 UA를 403으로 거르므로(사이트 정책) 읽지 않습니다. RSS만 사용.
    html_ok = None

    os.makedirs("raw", exist_ok=True)
    by_d = {}
    for it in entries:
        by_d.setdefault(bucket(it.pop("_dt")), []).append(it)
    oldest = min((e["publishedAt"] for e in entries), default=None)
    newest = max((e["publishedAt"] for e in entries), default=None)
    summary = {}
    for D, items in sorted(by_d.items()):
        p = f"raw/{D}.json"
        cur = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None
        d = datetime.strptime(D, "%Y-%m-%d").date()
        if not cur or "runs" not in cur:  # 새 형식으로 시작(구 형식 파일은 덮어씀)
            cur = {"date": D, "window": f"{d - timedelta(days=1)} 03:00 ~ {d} 03:00 (KST, 게시 시각 기준)",
                   "source": "GeekNews RSS (GitHub Actions 매시간 누적)", "runs": [], "items": []}
        have = {x["id"]: x for x in cur["items"]}
        added = 0
        for it in items:
            it["aiGuess"] = is_ai(it)
            it["alreadyPublished"] = it["id"] in used
            if it["id"] in have:
                have[it["id"]].update({k: v for k, v in it.items() if v})
            else:
                have[it["id"]] = it
                added += 1
        cur["items"] = sorted(have.values(), key=lambda x: x["publishedAt"])
        cur["runs"].append({"at": now.isoformat(timespec="seconds"), "rssUpdated": upd, "entries": len(items),
                            "added": added, "rssOldest": oldest, "rssNewest": newest, "htmlOk": html_ok})
        cur["runs"] = cur["runs"][-48:]
        # 빈틈 감지: 직전 실행의 최신 글보다 이번 RSS의 가장 오래된 글이 더 새로우면 놓친 글이 있을 수 있음
        prev = [r for r in cur["runs"][:-1] if r.get("rssNewest")]
        if prev and oldest and oldest > prev[-1]["rssNewest"]:
            cur.setdefault("gaps", []).append({"between": [prev[-1]["rssNewest"], oldest]})
        cur["updatedAt"] = now.isoformat(timespec="seconds")
        cur["counts"] = {"items": len(cur["items"]),
                         "candidates": sum(1 for x in cur["items"] if not x["alreadyPublished"]),
                         "aiGuess": sum(1 for x in cur["items"] if x["aiGuess"] and not x["alreadyPublished"])}
        cur["status"] = "ok"
        json.dump(cur, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        summary[D] = {"added": added, **cur["counts"]}
    print(json.dumps({"status": "ok", "rssUpdated": upd, "entries": len(entries), "files": summary,
                      "htmlOk": html_ok}, ensure_ascii=False))


if __name__ == "__main__":
    main()
