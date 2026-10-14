"""data/*.json 검증 + data/index.json(날짜 목록·트렌드 집계) 생성."""
import collections
import datetime
import glob
import json

CATS = ["모델 출시", "에이전트·개발도구", "인프라·하드웨어", "산업·비즈니스", "안전·정책", "연구", "사회·영향"]
REQ = ["rank", "id", "title", "category", "why", "easy", "normal", "original", "url"]


def check_visual(f, it):
    v = it.get("visual")
    if v is None:
        return
    where = (f, it["id"])
    assert v.get("type") in ("bars", "kpi"), where
    assert v.get("title"), where
    if v["type"] == "bars":
        items = v.get("items") or []
        assert 2 <= len(items) <= 6, where
        for x in items:
            assert x.get("label") and isinstance(x.get("value"), (int, float)) and x["value"] >= 0, where
        assert v.get("better") in ("higher", "lower", "neutral"), where
        if "highlight" in v:
            assert 0 <= v["highlight"] < len(items), where
    else:
        stats = v.get("stats") or []
        assert 1 <= len(stats) <= 4, where
        for x in stats:
            assert x.get("value") and x.get("label"), where


files = sorted(glob.glob("data/20??-??-??.json"), reverse=True)
dates = []
for f in files:
    d = json.load(open(f, encoding="utf-8"))
    assert 1 <= len(d["items"]) <= 7, f
    for it in d["items"]:
        for k in REQ:
            assert it.get(k), (f, it.get("id"), k)
        assert it["category"] in CATS, (f, it["id"], it["category"])
        check_visual(f, it)
    items = sorted(d["items"], key=lambda x: x["rank"])
    dates.append({
        "date": d["date"],
        "headline": d.get("headline", ""),
        "top3": [i["title"] for i in items[:3]],
        "catCounts": dict(collections.Counter(i["category"] for i in items)),
        "tags": [t for i in items for t in i.get("tags", [])],
    })

idx = {
    "updated": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="minutes"),
    "categories": CATS,
    "dates": dates,
}
json.dump(idx, open("data/index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(len(dates), [x["date"] for x in dates])
