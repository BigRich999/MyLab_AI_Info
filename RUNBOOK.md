# 매일 발간 런북 (자동 실행용)

이 파일은 매일 04:00 KST(실제 시작 03:57) 예약 작업이 따르는 절차입니다.

## 0. 날짜와 구간
- 발간일 D = 오늘(KST). 수집 구간 = 직전 발간 이후 ~ 실행 시점(대략 D-1 04:00 ~ D 04:00 KST).
- 이전 날짜 파일에 이미 실린 topic id는 제외해 빈틈과 중복을 막습니다. `window` 필드에는 실제 수집 구간을 적습니다.
- `data/D.json`이 이미 있으면 덮어씁니다(재실행 안전).

## 1. 수집
- WebFetch로 `https://news.hada.io/rss/news`(Atom)를 읽고, `published`가 구간 안에 있는 항목만 고릅니다.
- RSS에 구간 시작 이전 글이 다 안 나오면 `https://news.hada.io/past?day=D-1`(필요 시 &page=2,3)로 보충합니다.
- 셸(curl)은 news.hada.io에 접근할 수 없습니다. 반드시 WebFetch를 씁니다.
- 이미 이전 날짜 파일에 실린 topic id는 제외합니다(중복 방지).

## 2. 선별 (7개)
- AI·ML 관련 글만 후보로 둡니다.
- 가중치: 산업 파급력 40%, 기술적 새로움 25%, 실무 영향(개발도구·에이전트) 20%, 사회·정책·안전 15%.
- 같은 사건을 다룬 글은 하나로 묶습니다. 한 카테고리에 4개 이상 몰리지 않게 보정합니다.
- Show GN(개인 프로젝트)은 파급력이 클 때만 넣습니다.
- 1~3위가 메인 Top 3입니다.

## 3. 심화
- 각 토픽 페이지 `https://news.hada.io/topic?id=N`을 WebFetch로 읽습니다.
- '브라우저 확인' 화면이 나오면, RSS 요약과 WebSearch로 찾은 원 출처 기사를 대신 읽습니다.
- 사실·수치는 반드시 읽은 출처에 근거합니다. 원문 문장을 그대로 옮기지 않고 새로 씁니다.

## 4. 작성 — `data/D.json` 스키마
```json
{
  "date": "YYYY-MM-DD",
  "window": "YYYY-MM-DD 07:00 ~ YYYY-MM-DD 07:00 (KST)",
  "source": "GeekNews RSS",
  "generatedAt": "ISO8601+09:00",
  "headline": "그날의 흐름을 한 문장으로",
  "items": [{
    "rank": 1, "id": 35309, "title": "GeekNews 제목 그대로",
    "category": "모델 출시 | 에이전트·개발도구 | 인프라·하드웨어 | 산업·비즈니스 | 안전·정책 | 연구 | 사회·영향",
    "tags": ["3~4개"],
    "why": "AI 트렌드 관점에서 왜 중요한지 한 문장",
    "easy": "중학생용: 비유 1개 + 3~4문장, 전문용어 없이",
    "normal": "고등학생용: 배경 → 무엇이 새로운가 → 의미, 5~7문장, 용어는 풀어서",
    "original": "전공자용: '- **소제목**: 내용' 형식 bullet 5~7개. 수치·구조·한계·비판·맥락 포함",
    "terms": [{"term": "용어", "desc": "한 줄 풀이"}],
    "url": "https://news.hada.io/topic?id=N",
    "originalUrl": "원 출처 URL(모르면 url과 동일)"
  }]
}
```
- `python3 build_index.py`로 검증(항목 7개·필수 필드)하고 `data/index.json`을 다시 만듭니다.

## 5. 게시
- `git add -A && git commit && git push origin main` → GitHub Pages가 자동 반영합니다.
- 1~2분 뒤 `https://bigrich999.github.io/MyLab_AI_Info/data/D.json`이 열리는지 확인합니다.

## 6. 안내 메일 (웹 요약 화면과 동기화)
- `python3 build_email.py D` 를 실행합니다. 웹과 같은 `data/D.json`·같은 파스텔 디자인으로 `email/D.html`(본문), `email/D.txt`(텍스트 대체본), `email/D.subject.txt`(제목)를 만듭니다.
- 메일 내용을 손으로 쓰지 말고, 생성된 파일 내용을 그대로 보냅니다. 그래야 메일이 웹 화면과 항상 일치합니다.
- Gmail 커넥터 send_message: to=dr.jimi99@gmail.com, subject=email/D.subject.txt, htmlBody=email/D.html, body=email/D.txt.
- 메일의 각 항목 링크(`#D/easy/n{id}`)는 웹의 해당 카드로 바로 이동합니다.
- `email/` 폴더도 함께 커밋합니다(발송 기록).
