# 스킬잇 Daily 쿠버네티스 퀴즈

매일 쿠버네티스 학습 내용을 퀴즈로 확인하는 데일리 퀴즈 사이트입니다.

**사이트:** https://skilleat-labs.github.io/k8s-daily-quiz

---

## 구조

```
k8s-daily-quiz/
├── index.html         # 퀴즈 웹 페이지
├── daily_k8s.py       # 퀴즈 자동 생성 스크립트
├── quizzes/
│   └── YYYY-MM-DD.json  # 날짜별 퀴즈 데이터
└── requirements.txt
```

---

## 퀴즈 추가 방법

### 1. 환경 설정

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. 스크립트 실행

```bash
python daily_k8s.py
```

주제를 입력하면 자동으로:
1. AI가 학습 요약본 생성
2. 500글자 단위로 분할 (카톡 발송용)
3. 아침 인사말 생성
4. 퀴즈 JSON 생성 → `quizzes/YYYY-MM-DD.json` 저장
5. Git push
6. 카톡 메시지 클립보드 복사

### 3. 퀴즈 JSON 직접 작성

`quizzes/YYYY-MM-DD.json` 형식으로 직접 작성도 가능합니다.

```json
{
  "date": "2026-04-02",
  "title": "퀴즈 제목",
  "description": "오늘 배운 내용을 확인해보세요!",
  "questions": [
    {
      "id": 1,
      "type": "ox",
      "question": "질문 내용",
      "answer": true,
      "explanation": "해설 내용"
    },
    {
      "id": 2,
      "type": "multiple",
      "question": "질문 내용",
      "options": ["선택지1", "선택지2", "선택지3", "선택지4"],
      "answer": 0,
      "explanation": "해설 내용"
    }
  ]
}
```

- `type`: `"ox"` 또는 `"multiple"`
- `answer`: OX는 `true/false`, 4지선다는 `0~3` (인덱스)

---

## 퀴즈 접속 방법

- 오늘 퀴즈: `https://skilleat-labs.github.io/k8s-daily-quiz`
- 특정 날짜: `https://skilleat-labs.github.io/k8s-daily-quiz?date=2026-04-02`
