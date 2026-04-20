#!/usr/bin/env python3
"""
감테크 Daily K8s 자동화 스크립트
주제만 입력하면 → AI 요약 → 500글자 분할 → 인사말 → 퀴즈 JSON → git push → 클립보드 복사
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("❌ openai 패키지가 없습니다. 설치해주세요:")
    print("   pip install openai")
    sys.exit(1)

# ─── 설정 ───────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = "gpt-4o"
TODAY = datetime.now().strftime("%Y-%m-%d")

QUIZ_DIR = Path(__file__).parent / "quizzes"
REPO_DIR = Path(__file__).parent

QUIZ_URL = "https://skilleat-labs.github.io/k8s-daily-quiz"
MAX_CHARS = 500
# ────────────────────────────────────────────────────


def generate_greeting(client, topic):
    """매일 다른 아침 인사 + 응원 메시지"""
    print("🌅 인사말 생성 중...")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=300,
        temperature=0.9,
        messages=[
            {
                "role": "system",
                "content": "당신은 쿠버네티스 강사입니다. 수강생들에게 매일 아침 따뜻하고 동기부여가 되는 메시지를 보냅니다."
            },
            {
                "role": "user",
                "content": f"""카카오톡 오픈채팅방에 보낼 아침 인사말을 만들어줘.

## 조건
- 첫 줄은 반드시 "좋은 아침입니다."로 시작
- 두번째 줄에 쿠버네티스 학습을 하고 있는 수강생들에게 보내는 짧은 응원/격려 메시지 (1~2문장)
- 세번째 줄에 오늘의 주제({topic})를 안내하고, 읽어본 뒤 퀴즈까지 풀어보라는 말
- 경어체 사용 (~입니다, ~하세요)
- 이모지 사용하지 않기
- 마크다운 서식 없이 순수 텍스트
- 전체 3~5줄, 200글자 이내
- 매번 다른 표현을 사용해서 신선하게

## 출력
인사말만 출력. 다른 설명 없이."""
            }
        ]
    )
    return response.choices[0].message.content.strip()


def generate_summary(client, topic):
    """주제 키워드로 쿠버네티스 학습 요약본 생성"""
    print("📝 요약 생성 중...")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=3000,
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 10년 이상 쿠버네티스를 운영해온 현직 SRE 엔지니어이자 강사입니다. "
                    "이론보다 실무 경험을 바탕으로 설명하며, "
                    "초보자가 실제 운영 환경에서 겪는 문제와 오해를 짚어주는 방식으로 가르칩니다. "
                    "내용은 항상 기술적으로 정확하고 구체적이어야 합니다. "
                    "모든 내용은 쿠버네티스 공식 문서(kubernetes.io)를 근거로 하며, "
                    "deprecated되었거나 이미 제거된 기능(예: PodSecurityPolicy, dockershim 등)은 다루지 않습니다. "
                    "항상 현재 안정 버전(stable) 기준의 최신 정보를 사용하십시오."
                )
            },
            {
                "role": "user",
                "content": f"""아래 쿠버네티스 주제에 대해 카카오톡으로 보낼 학습 요약본을 만들어줘.

## 문체 규칙 (반드시 지켜야 함)
- 경어체 사용 (~입니다, ~됩니다, ~합니다)
- 이모지 절대 사용하지 않기
- 마크다운 서식(#, *, -, 번호 등) 사용하지 않기
- 순수 텍스트만, 문단 단위로 줄바꿈
- 전문 용어는 영어 그대로 사용 (Pod, Service, Deployment 등)

## 내용 규칙 (핵심)
- 단순 개념 나열이 아니라, 실무에서 왜 이것이 중요한지 맥락을 설명할 것
- 실제 운영 환경에서 자주 발생하는 장애 사례나 흔한 실수를 최소 1가지 포함
- "이렇게 설정하면 어떻게 되는가"처럼 동작 결과가 명확하게 드러나도록 서술
- 초보자가 자주 오해하는 부분을 명시적으로 짚어줄 것
- 관련 kubectl 명령어나 YAML 필드가 있다면 텍스트 안에 자연스럽게 언급

## 구조 규칙
- 개념 설명 → 실제 동작 흐름 → 실무 주의점/트러블슈팅 → 핵심 정리 순서로 서술
- 각 문단은 하나의 주제에 집중
- 추상적인 설명 대신 "실제로 무슨 일이 일어나는가"를 중심으로

## 참고 예시 (이 문체와 깊이를 따라해)
"쿠버네티스의 핵심은 원하는 상태를 선언하면, 그 상태를 실제로 맞추는 구조로 동작한다는 점입니다. 사용자가 Deployment와 같은 리소스를 생성하면, 이 요청은 API Server로 전달되고, etcd에 저장됩니다. 이때 우리는 실행을 명령하는 것이 아니라, 클러스터가 어떤 상태가 되길 원하는지 선언하는 것입니다. 실무에서는 이 차이를 모르고 Pod가 재시작될 때마다 kubectl run으로 직접 생성하려다 Deployment의 replicas 설정과 충돌하는 상황이 종종 발생합니다."

## 분량
- 전체 1500~2000글자 사이 (절대 2000글자를 넘지 말 것)

## 주제
{topic}"""
            }
        ]
    )
    return response.choices[0].message.content


def split_text(text, max_chars=MAX_CHARS, max_chunks=5):
    """텍스트를 max_chars 이하로 분할 (최대 max_chunks개)"""
    chunks = []
    current = ""

    for line in text.split("\n"):
        if not line.strip():
            if current:
                if len(current) + 1 <= max_chars:
                    current += "\n"
                else:
                    chunks.append(current.strip())
                    current = ""
            continue

        test = current + ("\n" if current else "") + line
        if len(test) > max_chars:
            if current.strip():
                chunks.append(current.strip())
            if len(line) > max_chars:
                sentences = line.replace(". ", ".\n").split("\n")
                for sent in sentences:
                    if current and len(current + " " + sent) <= max_chars:
                        current += " " + sent
                    else:
                        if current.strip():
                            chunks.append(current.strip())
                        current = sent
            else:
                current = line
        else:
            current = test

    if current.strip():
        chunks.append(current.strip())

    # 최대 개수 초과 시 마지막 청크들을 합쳐서 max_chunks 개로 맞춤
    if len(chunks) > max_chunks:
        merged_last = "\n\n".join(chunks[max_chunks - 1:])
        chunks = chunks[:max_chunks - 1] + [merged_last]

    return chunks


def generate_quiz(client, summary, title_hint=""):
    """요약본 기반으로 퀴즈 JSON 생성"""
    print("🧩 퀴즈 생성 중...")
    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=2500,
        temperature=0.3,
        messages=[
            {
                "role": "system",
                "content": (
                    "당신은 쿠버네티스 자격증 시험 및 실무 인터뷰 문제를 출제해온 전문가입니다. "
                    "좋은 문제는 단순 암기가 아닌 개념의 정확한 이해와 실무 판단력을 테스트합니다. "
                    "오답 보기는 실제로 헷갈릴 만한 것이어야 하며, 해설은 틀린 이유까지 명확히 설명해야 합니다. "
                    "모든 문제는 쿠버네티스 공식 문서(kubernetes.io)를 근거로 하며, "
                    "deprecated되었거나 이미 제거된 기능은 출제하지 않습니다. "
                    "항상 현재 안정 버전(stable) 기준의 최신 정보를 사용하십시오."
                )
            },
            {
                "role": "user",
                "content": f"""아래 쿠버네티스 학습 요약본을 기반으로 퀴즈 JSON을 만들어줘.

## 조건
- OX 퀴즈 3문제, 4지선다 2문제 (총 5문제)
- 난이도: 실무/운영 환경에서 마주칠 수 있는 상황 기반
  - OX: 실무에서 흔히 오해하는 개념, 장애 상황에서의 동작 방식, 운영 시 주의점 위주
  - 4지선다: 실제 kubectl 명령어, 트러블슈팅 상황, YAML 설정값 선택 등 구체적인 실무 시나리오 기반
- OX 문제는 true/false가 골고루 섞이게 (단순한 "~이다/아니다" 말고 조건부 상황으로 출제)
- 4지선다 오답은 실무에서 헷갈리기 쉬운 것으로 구성 (단순 오타나 말도 안 되는 보기 금지)
- 해설(explanation)은 정답 이유 + 나머지 보기가 왜 틀렸는지까지 포함해서 2~3문장으로 설명
- 한국어로 작성
- 코드블록이나 마크다운 없이 순수 JSON만 출력

## 출력 형식
{{
  "date": "{TODAY}",
  "title": "{title_hint}",
  "description": "오늘 배운 내용을 확인해보세요!",
  "questions": [
    {{"id": 1, "type": "ox", "question": "...", "answer": true, "explanation": "..."}},
    {{"id": 2, "type": "ox", "question": "...", "answer": false, "explanation": "..."}},
    {{"id": 3, "type": "ox", "question": "...", "answer": true, "explanation": "..."}},
    {{"id": 4, "type": "multiple", "question": "...", "options": ["A", "B", "C", "D"], "answer": 0, "explanation": "..."}},
    {{"id": 5, "type": "multiple", "question": "...", "options": ["A", "B", "C", "D"], "answer": 1, "explanation": "..."}}
  ]
}}

## 요약본
{summary}"""
            }
        ]
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]

    return json.loads(raw.strip())


def git_push(quiz_path):
    """퀴즈 JSON git push"""
    print("🚀 Git push 중...")
    os.chdir(REPO_DIR)
    subprocess.run(["git", "add", str(quiz_path)], check=True)
    subprocess.run(["git", "commit", "-m", f"quiz: {TODAY}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("✅ Push 완료!")


def copy_to_clipboard(text):
    """Mac 클립보드에 복사"""
    process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    process.communicate(text.encode("utf-8"))


def main():
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY 환경변수를 설정해주세요:")
        print('   export OPENAI_API_KEY="sk-..."')
        sys.exit(1)

    # 주제 입력 (커맨드라인 또는 대화형)
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        print("")
        print("[감테크 Daily K8s]")
        print("오늘의 쿠버네티스 주제를 입력하세요.")
        print("예: Service와 ClusterIP, NodePort 개념")
        print("")
        topic = input("주제 입력> ").strip()
        if not topic:
            print("주제를 입력해주세요.")
            sys.exit(1)

    print(f"\n주제: {topic}")
    print("=" * 50)

    client = OpenAI(api_key=OPENAI_API_KEY)

    # 1. AI 요약 생성
    summary = generate_summary(client, topic)
    print(f"✅ 요약 완료 ({len(summary)}글자)")

    # 2. 500글자 분할
    chunks = split_text(summary)
    print(f"✂️  {len(chunks)}개 메시지로 분할 완료")
    for i, chunk in enumerate(chunks, 1):
        print(f"   [{i}/{len(chunks)}] {len(chunk)}글자")

    # 3. 인사말 생성
    greeting = generate_greeting(client, topic)
    print(f"✅ 인사말 생성 완료")

    # 4. 퀴즈 JSON 생성 (요약본 기반)
    QUIZ_DIR.mkdir(exist_ok=True)
    quiz_data = generate_quiz(client, summary, topic)

    # 같은 날 여러 번 실행 시 덮어쓰지 않고 순번 추가 (예: 2026-04-21-2.json)
    quiz_path = QUIZ_DIR / f"{TODAY}.json"
    if quiz_path.exists():
        n = 2
        while (QUIZ_DIR / f"{TODAY}-{n}.json").exists():
            n += 1
        quiz_path = QUIZ_DIR / f"{TODAY}-{n}.json"

    quiz_path.write_text(json.dumps(quiz_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 퀴즈 저장: {quiz_path.name}")

    # 5. Git push
    try:
        git_push(quiz_path)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Git push 실패: {e}")
        print("   수동으로 push 해주세요.")

    # 6. 카톡 발송 메시지 구성
    #    인사말 → 요약1 → 요약2 → ... → 마지막 요약 + 퀴즈링크
    quiz_link = f"{QUIZ_URL}/?date={quiz_path.stem}"

    messages = []
    messages.append(("인사말", greeting))
    for i, chunk in enumerate(chunks, 1):
        if i == len(chunks):
            # 마지막 요약에 퀴즈 링크 붙이기
            chunk_with_quiz = chunk + f"\n\n오늘의 퀴즈입니다. 위 내용을 읽어보신 뒤 풀어보세요.\n{quiz_link}"
            messages.append((f"요약 {i}/{len(chunks)} + 퀴즈", chunk_with_quiz))
        else:
            messages.append((f"요약 {i}/{len(chunks)}", chunk))

    # 미리보기
    print("\n" + "=" * 50)
    print("📋 카톡 발송 메시지 미리보기")
    print("=" * 50)

    for i, (label, msg) in enumerate(messages, 1):
        print(f"\n--- [{i}] {label} ({len(msg)}글자) ---")
        print(msg)

    # 메시지별 복사
    print(f"\n" + "=" * 50)
    print(f"💡 번호 입력 → 클립보드 복사 → 카톡에 ⌘V")
    for i, (label, _) in enumerate(messages, 1):
        print(f"   {i}) {label}")
    print(f"   q) 종료")

    while True:
        choice = input("\n복사할 번호: ").strip()
        if choice.lower() == "q":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(messages):
                label, msg = messages[idx]
                copy_to_clipboard(msg)
                print(f"✅ [{label}] 복사 완료! 카톡에 ⌘V")
            else:
                print("잘못된 번호입니다.")
        except ValueError:
            print("숫자를 입력해주세요.")

    print("\n🎉 오늘의 데일리 발송 완료!")


if __name__ == "__main__":
    main()