"""GeekNews 수집기 (GitHub Actions에서 실행).

클라우드 예약 작업은 news.hada.io에 직접 접근할 수 없으므로, GitHub 서버가 먼저
아카이브·최신글·RSS·토픽 페이지를 받아 raw/D.json 으로 저장합니다.
예약 작업은 이 파일만 읽고 선별·작성합니다.

사용: python3 tools/collect.py [YYYY-MM-DD]   (생략 시 오늘, Asia/Seoul)
종료 코드: 0 정상, 2 차단·수집 실패(파일은 status와 함께 저장됨)
"""
import glob, html, json, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))
BASE = "https://news.hada.io"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36 ai-trend-daily-collector")
AI_KW = [
    "ai", "a.i", "llm", "gpt", "openai", "anthropic", "claude", "gemini", "deepmind", "llama",
    "mistral", "deepseek", "qwen", "copilot", "cursor", "mcp", "agent", "rag", "embedding",
    "transformer", "diffusion", "nvidia", "gpu", "tpu", "cuda", "hugging", "inference",
    "prompt", "chatbot", "grok", "xai", "codex", "perplexity", "midjourney", "sora",
    "인공지능", "에이전트", "모델", "생성형", "머신러닝", "딥러닝", "학습", "추론", "챗봇",
    "프롬프트", "데이터센터", "반도체", "로봇", "자율주행", "벡터", "파인튜닝", "바이브",
]
BLOCK_MARKERS = ["cf-chl", "challenge-platform", "Just a moment", "브라우저 확인",
                 "Checking your browser", "captcha"]


def fetch(url, log):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko,en;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read().decode("utf-8", "replace")
            code = r.status
    except urllib.error.HTTPError as e:
        body, code = e.read().decode("utf-8", "replace"), e.code
    except Exception as e:  # 네트워크 오류
        log.append({"url": url, "status": "error", "detail": str(e)[:200]})
        return None
    blocked = code != 200 or any(m.lower() in body.lower() for m in BLOCK_MARKERS)
    log.append({"url": url, "status": "blocked" if blocked else "ok", "http": code, "bytes": len(body)})
    time.sleep(1.0)
    return None if blocked else body


def text(s):
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", s, flags=re.I)
    s = re.sub(r"<br\s*/?>|</p>|</li>|</h\d>|</div>", "\n", s, flags=re.I)
    s = re.sub(r"<li[^>]*>", "\n- ", s, flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    s = re.sub(r"[ \t\u00a0]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n", s).strip()


def parse_list(body, where):
    """아카이브/최신글 목록에서 글 정보를 뽑습니다."""
    out = {}
    chunks = re.split(r"class=['\"]?topic_row", body)
    chunks = chunks[1:] if len(chunks) > 1 else [body]
    for ch in chunks:
        ids = re.findall(r"topic\?id=(\d+)", ch)
        if not ids:
            continue
        if len(chunks) == 1:  # 구조를 못 찾으면 id만 수집
            for i in dict.fromkeys(ids):
                out.setdefault(int(i), {"id": int(i), "seenOn": [where]})
            break
        tid = int(ids[0])
        h1 = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", ch)
        desc = re.search(r"class=['\"]?topicdesc[^>]*>([\s\S]*?)</div>", ch)
        pts = re.search(r"id=['\"]?tp\d+['\"]?[^>]*>(\d+)", ch)
        cmt = re.search(r"댓글\s*(\d+)", ch)
        orig = re.search(r"class=['\"]?topictitle[^>]*>\s*<a[^>]*href=['\"]?([^'\" >]+)", ch)
        info = re.search(r"class=['\"]?topicinfo[^>]*>([\s\S]*?)</div>", ch)
        out[tid] = {
            "id": tid,
            "title": text(h1.group(1)) if h1 else None,
            "listDesc": text(desc.group(1))[:300] if desc else None,
            "points": int(pts.group(1)) if pts else None,
            "comments": int(cmt.group(1)) if cmt else 0,
            "originalUrl": html.unescape(orig.group(1)) if orig else None,
            "info": text(info.group(1))[:120] if info else None,
            "seenOn": [where],
        }
    return out


def parse_topic(body):
    t = re.search(r"<title>([\s\S]*?)</title>", body)
    title = re.sub(r"\s*\|\s*GeekNews\s*$", "", text(t.group(1))) if t else None
    ogd = re.search(r"<meta[^>]+property=['\"]og:description['\"][^>]+content=['\"]([^'\"]*)", body)
    orig = re.search(r"class=['\"]?topictitle[^>]*>\s*<a[^>]*href=['\"]?([^'\" >]+)", body)
    m = re.search(r"(id|class)=['\"]?topic_contents", body)
    if m:
        seg = body[m.start():]
        end = re.search(r"class=['\"]?(comment_thread|commentTD|comment_row)|id=['\"]?comment", seg)
        seg = seg[: end.start()] if end else seg[:60000]
        content = text("<x " + seg)
    else:
        content = text(body)
    when = re.search(r"(20\d\d-\d\d-\d\d[ T]\d\d:\d\d(:\d\d)?)", body)
    return {
        "title": title,
        "ogDescription": html.unescape(ogd.group(1)) if ogd else None,
        "originalUrl": html.unescape(orig.group(1)) if orig else None,
        "postedAt": when.group(1) if when else None,
        "content": content[:6000],
    }


def is_ai(item):
    s = " ".join(str(item.get(k) or "") for k in ("title", "listDesc")).lower()
    return any(re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", s) if k.isascii() else k in s for k in AI_KW)


def main():
    now = datetime.now(KST)
    D = sys.argv[1] if len(sys.argv) > 1 else now.strftime("%Y-%m-%d")
    d = datetime.strptime(D, "%Y-%m-%d").date()
    used, pubs = set(), []
    for f in glob.glob("data/20??-??-??.json"):
        j = json.load(open(f, encoding="utf-8"))
        if j["date"] >= D:
            continue
        pubs.append(j["date"])
        used |= {it["id"] for it in j["items"]}
    last = max(pubs) if pubs else None
    # 결정(2026-11-20): 긴 공백은 메우지 않음 → 직전 발간일과 D-1 중 늦은 날부터 수집
    start = max(datetime.strptime(last, "%Y-%m-%d").date(), d - timedelta(days=1)) if last else d - timedelta(days=1)
    days = [(start + timedelta(days=i)).isoformat() for i in range((d - start).days + 1)]

    log, items = [], {}
    pages = [(f"{BASE}/past?day={day}" + (f"&page={p}" if p > 1 else ""), f"past:{day}")
             for day in days for p in (1, 2, 3)]
    pages += [(f"{BASE}/new", "new"), (f"{BASE}/new?page=2", "new")]
    for url, where in pages:
        body = fetch(url, log)
        if not body:
            continue
        got = parse_list(body, where)
        if not got and "&page=" in url:
            continue
        for tid, it in got.items():
            if tid in items:
                items[tid]["seenOn"] = sorted(set(items[tid]["seenOn"] + it["seenOn"]))
                for k, v in it.items():
                    if items[tid].get(k) in (None, "") and v:
                        items[tid][k] = v
            else:
                items[tid] = it

    # RSS(보조): 신선도만 기록, 신선하면 제목 보충
    rss = fetch(f"{BASE}/rss/news", log)
    rss_info = {"updated": None, "fresh": False}
    if rss:
        u = re.search(r"<updated>([^<]+)</updated>", rss)
        rss_info["updated"] = u.group(1) if u else None
        try:
            upd = datetime.fromisoformat(rss_info["updated"].replace("Z", "+00:00"))
            rss_info["fresh"] = upd >= datetime.combine(d - timedelta(days=1), datetime.min.time(), KST)
        except Exception:
            pass
        if rss_info["fresh"]:
            for e in re.findall(r"<entry>([\s\S]*?)</entry>", rss):
                i = re.search(r"topic\?id=(\d+)", e)
                t = re.search(r"<title[^>]*>([\s\S]*?)</title>", e)
                if i and int(i.group(1)) not in items:
                    items[int(i.group(1))] = {"id": int(i.group(1)), "title": text(t.group(1)) if t else None,
                                              "seenOn": ["rss"]}

    cands = [it for tid, it in sorted(items.items()) if tid not in used]
    for it in cands:
        it["url"] = f"{BASE}/topic?id={it['id']}"
        it["aiGuess"] = is_ai(it) if it.get("title") else True
    for it in cands:
        if not it["aiGuess"]:
            continue
        body = fetch(it["url"], log)
        if body:
            tp = parse_topic(body)
            it["topic"] = tp
            it["title"] = it.get("title") or tp["title"]
            it["originalUrl"] = it.get("originalUrl") or tp["originalUrl"]
            it["aiGuess"] = is_ai(it)
    list_ok = sum(1 for l in log if l["status"] == "ok" and "/topic?" not in l["url"] and "/rss/" not in l["url"])
    status = "ok" if list_ok and cands else ("blocked" if any(l["status"] != "ok" for l in log) else "empty")
    out = {
        "date": D,
        "collectedAt": now.isoformat(timespec="seconds"),
        "lastPublished": last,
        "days": days,
        "window": f"{days[0]} 00:00 ~ {now.strftime('%Y-%m-%d %H:%M')} (KST, 아카이브 날짜 기준)",
        "status": status,
        "rss": rss_info,
        "counts": {"listed": len(items), "excludedUsed": len(items) - len(cands), "candidates": len(cands),
                   "aiGuess": sum(1 for c in cands if c["aiGuess"]),
                   "topicFetched": sum(1 for c in cands if "topic" in c)},
        "fetchLog": log,
        "items": cands,
    }
    import os
    os.makedirs("raw", exist_ok=True)
    json.dump(out, open(f"raw/{D}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("date", "status", "window", "rss", "counts")}, ensure_ascii=False))
    sys.exit(0 if status == "ok" else 2)


if __name__ == "__main__":
    main()
