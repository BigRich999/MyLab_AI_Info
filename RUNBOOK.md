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
### 숫자 시각화 `visual` (선택, 가능하면 작성)
원문에 비교할 만한 숫자가 있는 뉴스에만 붙입니다. 숫자가 없으면 넣지 않습니다(억지로 만들지 말 것).
- 막대 비교(같은 단위 2~6개):
```json
"visual": {"type":"bars","title":"무엇을 비교하는지","unit":"초","better":"lower|higher|neutral",
  "items":[{"label":"Git","value":426,"display":"7.1분"},{"label":"Scion","value":5.1,"display":"5.1초"}],
  "highlight":1, "note":"측정 조건·출처(예: 회사 자체 측정)"}
```
  - `value`는 같은 단위의 숫자(그래프 길이), `display`는 화면에 보일 글자. 단위가 다른 값은 한 막대 차트에 섞지 않습니다.
  - `highlight`는 강조할 막대 번호(0부터, 생략 시 전체 강조).
- 숫자 카드(핵심 수치 1~4개):
```json
"visual": {"type":"kpi","title":"한눈에 보기","stats":[{"value":"800+","label":"MCP 서버","sub":"보조 설명"}],"note":"출처"}
```
- 모든 숫자는 읽은 출처에 실제로 있는 값만 씁니다. 회사 자체 발표·추산이면 `note`에 밝힙니다.

### 작동 원리 도식 `diagram` (권장, 대부분의 뉴스에 작성)
"어떻게 작동하나/무엇이 바뀌었나"를 상자와 화살표로 보여줍니다. 순수 투자·인사 소식처럼 구조가 없으면 생략합니다.
노드: `{"label":"짧은 이름","sub":"한 줄 보충(모든 난이도에 표시)","detail":"전공자용 세부(Original에서만 표시)","kind":"input|proc|result|risk|actor"}`
- kind 색: input=입력(하늘), proc=처리(라벤더), result=결과(민트), risk=문제·위험(코랄), actor=사람·주체(버터)
- 네 가지 틀 중 하나:
```json
{"type":"flow","title":"…","nodes":[노드 3~6개],"caption":"한 줄 요약","cycle":false}
{"type":"compare","title":"…","before":{"title":"기존","nodes":[1~4개]},"after":{"title":"새 방식","nodes":[1~4개]},"caption":"…"}
{"type":"hub","title":"…","center":노드,"left":[1~4개],"right":[1~4개],"leftLabel":"왼쪽 묶음 이름","rightLabel":"오른쪽 묶음 이름","caption":"…"}
{"type":"layers","title":"…","layers":[위→아래 2~6개],"caption":"…"}
```
- 고르는 기준: 단계·순서 → flow(되돌아오는 순환이면 cycle:true), 전후 비교 → compare, 가운데 중계·플랫폼 → hub, 계층·피라미드 → layers.
- label은 12자 안팎으로 짧게, 숫자·사실은 출처에 있는 것만 씁니다. visual(숫자 카드)과 같은 숫자를 반복하지 않도록 합니다.

- `python3 build_index.py`로 검증(항목 수·필수 필드·카테고리·visual·diagram 형식)하고 `data/index.json`(트렌드 집계 포함)을 다시 만듭니다.
- 카테고리는 반드시 7개 중 하나: 모델 출시, 에이전트·개발도구, 인프라·하드웨어, 산업·비즈니스, 안전·정책, 연구, 사회·영향.

## 5. 게시
- `git add -A && git commit && git push origin main` → GitHub Pages가 자동 반영합니다.
- 1~2분 뒤 `https://bigrich999.github.io/MyLab_AI_Info/data/D.json`이 열리는지 확인합니다.

## 6. 안내 메일 (웹 요약 화면과 동기화)
- `python3 build_email.py D` 를 실행합니다. 웹과 같은 `data/D.json`·같은 파스텔 디자인으로 `email/D.html`(본문), `email/D.txt`(텍스트 대체본), `email/D.subject.txt`(제목)를 만듭니다.
- 메일 내용을 손으로 쓰지 말고, 생성된 파일 내용을 그대로 보냅니다. 그래야 메일이 웹 화면과 항상 일치합니다.
- Gmail 커넥터 send_message: to=dr.jimi99@gmail.com, subject=email/D.subject.txt, htmlBody=email/D.html, body=email/D.txt.
- 메일의 각 항목 링크(`#D/easy/n{id}`)는 웹의 해당 카드로 바로 이동합니다.
- `email/` 폴더도 함께 커밋합니다(발송 기록).
