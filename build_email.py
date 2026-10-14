"""웹의 '요약 화면'과 같은 데이터·같은 디자인으로 안내 메일을 만든다.

사용법: python3 build_email.py 2026-10-15
출력:  email/2026-10-15.html (메일 htmlBody), email/2026-10-15.txt (텍스트 대체본),
       email/2026-10-15.subject.txt (제목)

웹(index.html)과 같은 data/D.json을 읽으므로, 메일 내용은 항상 웹 화면과 일치한다.
카테고리 색과 파스텔 팔레트도 index.html의 값과 동일하게 맞춘다.
"""
import html
import json
import os
import re
import sys

SITE = "https://bigrich999.github.io/MyLab_AI_Info/"

# index.html의 CAT 팔레트와 동일
CAT = {
    "모델 출시": ("#c95c53", "#fde8e5"),
    "에이전트·개발도구": ("#3f72c4", "#e5eefd"),
    "인프라·하드웨어": ("#a8740f", "#fff1d6"),
    "산업·비즈니스": ("#2f8f67", "#e2f5ec"),
    "안전·정책": ("#7c55c4", "#f0e9fc"),
    "연구": ("#c04a86", "#ffe6f1"),
    "사회·영향": ("#0f8aa6", "#e3f4f7"),
}
INK, INK2, INK3 = "#2f2b3a", "#5d586b", "#9a94a8"
RULE, BG, PAPER = "#eee8f5", "#f8f5fc", "#ffffff"
ACCENT, ACCENT_SOFT = "#e9776e", "#fde8e5"
EASY, EASY_SOFT = "#3fa77c", "#e2f5ec"
NORMAL, NORMAL_SOFT = "#4f86d9", "#e5eefd"
ORIG, ORIG_SOFT = "#9670d6", "#f0e9fc"
FONT = "-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Noto Sans KR','Malgun Gothic',sans-serif"
WEEK = "월화수목금토일"


def e(s):
    return html.escape(str(s or ""), quote=True)


def link(date, level="easy", item=None):
    return f"{SITE}#{date}/{level}" + (f"/n{item}" if item else "")


def cat_chip(c):
    ink, bg = CAT.get(c, (INK2, "#f3eefa"))
    return (f'<span style="display:inline-block;font-size:12px;font-weight:700;border-radius:999px;'
            f'padding:2px 10px;background:{bg};color:{ink}">{e(c)}</span>')


def rank_badge(r, top):
    if top:
        return (f'<td width="44" valign="top" style="padding-right:12px"><div style="width:40px;height:40px;'
                f'line-height:40px;text-align:center;border-radius:12px;background:{ACCENT_SOFT};color:{ACCENT};'
                f'font-weight:900;font-size:19px">{r}</div></td>')
    return (f'<td width="36" valign="top" style="padding-right:10px"><div style="width:30px;height:30px;'
            f'line-height:30px;text-align:center;border-radius:10px;background:#f3eefa;color:{INK3};'
            f'font-weight:900;font-size:14px">{r}</div></td>')


def build(date):
    d = json.load(open(f"data/{date}.json", encoding="utf-8"))
    items = sorted(d["items"], key=lambda x: x["rank"])
    top, rest = items[:3], items[3:]
    y, m, dd = map(int, date.split("-"))
    import datetime
    wk = WEEK[datetime.date(y, m, dd).weekday()]
    hero = "background:#fde8e5;background-image:linear-gradient(120deg,#fde8e5 0%,#f0e9fc 45%,#e5eefd 75%,#e2f5ec 100%)"

    top_html = ""
    for it in top:
        top_html += f'''
<tr><td style="padding:0 0 16px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER};border:1px solid {RULE};border-radius:20px;border-collapse:separate">
<tr><td style="height:6px;border-radius:20px 20px 0 0;{hero};font-size:0;line-height:0">&nbsp;</td></tr>
<tr><td style="padding:20px 22px 18px">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr>{rank_badge(it["rank"], True)}
  <td valign="top">{cat_chip(it["category"])}
    <div style="font-size:18px;font-weight:800;line-height:1.45;color:{INK};margin-top:6px">{e(it["title"])}</div></td></tr></table>
  <div style="margin-top:12px;padding:10px 14px;background:{ACCENT_SOFT};border-radius:12px;font-size:14px;line-height:1.6;color:{INK2}"><b style="color:{ACCENT}">왜 중요?</b> {e(it["why"])}</div>
  <div style="margin-top:12px;padding:12px 16px;background:{EASY_SOFT};border-radius:14px">
    <span style="display:inline-block;font-size:11px;letter-spacing:.5px;color:{EASY};background:{PAPER};border-radius:999px;padding:1px 9px">EASY 설명</span>
    <div style="font-size:15.5px;line-height:1.8;color:{INK};margin-top:6px">{e(it["easy"])}</div>
  </div>
  <div style="margin-top:12px;font-size:13px">
    <a href="{e(it["url"])}" style="color:{INK3};text-decoration:none">GeekNews 원문 보기 ↗</a>
  </div>
</td></tr></table>
</td></tr>'''

    rest_html = ""
    for it in rest:
        rest_html += f'''
<tr><td style="padding:12px 0;border-top:1px dashed #e0d8ec">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr>{rank_badge(it["rank"], False)}
  <td valign="top">{cat_chip(it["category"])}
    <div style="margin-top:4px;font-size:15.5px;font-weight:800;line-height:1.5;color:{INK}">{e(it["title"])}</div>
    <div style="font-size:13.5px;line-height:1.6;color:{INK2};margin-top:2px">{e(it["why"])}</div></td></tr></table>
</td></tr>'''

    level_btns = "".join(
        f'<a href="{link(date, lv)}" style="display:inline-block;margin:0 3px;padding:7px 14px;border-radius:999px;'
        f'background:{soft};color:{ink};font-size:13px;font-weight:700;text-decoration:none">● {name}</a>'
        for lv, name, ink, soft in [("easy", "Easy", EASY, EASY_SOFT), ("normal", "Normal", NORMAL, NORMAL_SOFT),
                                    ("original", "Original", ORIG, ORIG_SOFT)])

    body = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{BG}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};font-family:{FONT}"><tr><td align="center" style="padding:20px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:640px">

<tr><td style="{hero};border-radius:20px;padding:22px 24px">
  <div style="font-size:11px;letter-spacing:2px;color:{ACCENT};font-family:ui-monospace,monospace">DAILY · GEEKNEWS AI PICKS</div>
  <div style="font-size:28px;font-weight:900;color:{INK};letter-spacing:-.5px;margin-top:2px">AI <span style="color:{ACCENT}">트렌드</span> 데일리</div>
  <div style="font-size:13px;color:{INK2};margin-top:4px">{y}년 {m}월 {dd}일 ({wk}) · 오늘의 AI 뉴스 {len(items)}개</div>
</td></tr>

<tr><td style="padding:16px 0">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER};border:1px solid {RULE};border-radius:20px;border-collapse:separate"><tr><td style="padding:18px 22px">
  <div style="font-size:12px;color:{INK3};font-family:ui-monospace,monospace">수집 구간: {e(d.get("window", ""))}</div>
  <div style="font-size:20px;font-weight:900;line-height:1.45;color:{INK};margin:6px 0 14px">{e(d.get("headline", ""))}</div>
  <a href="{link(date)}" style="display:inline-block;background:{ACCENT};color:#fff;text-decoration:none;font-weight:700;font-size:15px;padding:11px 22px;border-radius:999px">웹에서 오늘의 뉴스 보기 →</a>
  <div style="margin-top:10px;font-size:12px;color:{INK3}">웹에서 Easy · Normal · Original 난이도를 바꿔 가며 볼 수 있습니다.</div>
</td></tr></table>
</td></tr>

<tr><td style="font-size:13px;font-weight:700;color:{INK3};padding:4px 2px 10px">오늘의 Top 3</td></tr>
{top_html}

<tr><td style="padding:4px 0 16px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{PAPER};border:1px solid {RULE};border-radius:20px;border-collapse:separate"><tr><td style="padding:14px 22px 6px">
  <div style="font-size:13px;font-weight:700;color:{INK3};padding-bottom:4px">함께 볼 뉴스</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{rest_html}</table>
</td></tr></table>
</td></tr>

<tr><td style="font-size:12px;line-height:1.7;color:{INK3};padding:4px 6px 20px">
  이 메일은 웹과 같은 데이터에서 자동으로 만들어져, 웹 화면과 내용이 같습니다.<br>
  매일 새벽 4시경 새 뉴스가 발간됩니다. 출처: GeekNews
</td></tr>
</table></td></tr></table></body></html>'''

    lines = [f"[AI 트렌드 데일리] {m}월 {dd}일 ({wk})", d.get("headline", ""), "",
             f"웹에서 보기: {link(date)}", "", "■ 오늘의 Top 3"]
    for it in top:
        lines += [f"{it['rank']}. {it['title']} [{it['category']}]", f"  왜 중요? {it['why']}",
                  f"  {it['easy']}", ""]
    lines.append("■ 함께 볼 뉴스")
    for it in rest:
        lines.append(f"{it['rank']}. {it['title']}")
    lines += ["", "매일 새벽 4시경 새 뉴스가 발간됩니다. 출처: GeekNews"]

    short = re.split(r"[,，]", d.get("headline", ""))[0].strip()
    subject = f"[AI 트렌드 데일리] {m}월 {dd}일 — {short}"

    os.makedirs("email", exist_ok=True)
    open(f"email/{date}.html", "w", encoding="utf-8").write(body)
    open(f"email/{date}.txt", "w", encoding="utf-8").write("\n".join(lines))
    open(f"email/{date}.subject.txt", "w", encoding="utf-8").write(subject)
    print(subject)
    print(f"email/{date}.html ({len(body):,} bytes)")


if __name__ == "__main__":
    build(sys.argv[1])
