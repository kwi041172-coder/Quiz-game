# 별빛 탐험대: 천문학 퀴즈

태양계와 우주에 관한 문제를 풀고, 직접 문제를 등록해 나만의 퀴즈 모음을 키워 가는 Python 콘솔 게임입니다. Python 표준 라이브러리만 사용하며, 퀴즈와 점수는 JSON 파일에 저장됩니다.

## 주제 선정 이유

우주와 천문학은 익숙한 태양계부터 은하까지 폭넓게 탐구할 수 있고, 퀴즈로 과학 지식을 재미있게 확인할 수 있는 주제입니다. 기본 퀴즈에는 태양계 행성, 태양, 지구 대기, 우리은하에 관한 문제가 들어 있습니다.

## 실행 방법

Python 3.10 이상이 설치되어 있어야 합니다. 저장소의 루트 폴더에서 다음 명령을 실행합니다.

```text
python main.py
```

테스트는 외부 패키지 설치 없이 실행할 수 있습니다.

```text
python -m unittest -v
```

## 기능

- 메뉴에서 퀴즈 풀기, 추가, 목록 확인, 최고 점수 확인, 기록 확인, 삭제, 종료
- 기본 천문학 퀴즈 8개 제공
- 퀴즈 순서를 무작위로 섞고, 한 번에 풀 문제 수 선택
- 문제, 선택지 4개, 정답 번호, 힌트를 포함한 새 퀴즈 등록
- 힌트 사용 시 점수 1점 차감
- 최고 점수와 플레이 날짜·정답 수·힌트 사용 횟수 기록
- UTF-8 JSON 저장, 재실행 시 데이터 불러오기
- 빈 입력, 숫자 변환 실패, 허용 범위 밖 입력을 안내하고 다시 입력
- Ctrl+C와 입력 종료(EOF) 시 저장을 시도하고 안전하게 종료
- 저장 파일이 없으면 기본 데이터 사용, 손상된 파일이면 알림 후 기본 데이터로 복구
- 저장 도중 오류가 나면 이유를 알리고 임시 파일 정리를 시도

## 파일 구조

```text
Quiz-game/
├── main.py       # Quiz 및 QuizGame 클래스와 게임 실행 코드
├── test_main.py  # 표준 unittest 테스트
├── README.md     # 프로젝트 안내
├── .gitignore    # Python 캐시와 개인 저장 데이터 제외
└── state.json    # 첫 실행 후 자동 생성되는 게임 데이터
```

## 데이터 파일

`state.json`은 프로젝트 루트에 UTF-8로 생성됩니다. 개인별 퀴즈, 최고 점수, 게임 기록을 저장하며, 예시는 다음과 같습니다.

```json
{
  "quizzes": [
    {
      "question": "태양계에서 태양에 가장 가까운 행성은 무엇일까요?",
      "choices": ["금성", "수성", "지구", "화성"],
      "answer": 2,
      "hint": "태양계에서 가장 작은 행성이기도 합니다."
    }
  ],
  "best_score": 100,
  "best_correct": 1,
  "best_total": 1,
  "has_played": true,
  "history": [
    {
      "played_at": "2026-11-10T19:30:00+09:00",
      "total": 1,
      "correct": 1,
      "hints_used": 0,
      "score": 100
    }
  ]
}
```

- `quizzes`: 퀴즈 목록. `answer`는 1부터 4까지의 선택지 번호입니다.
- `best_score`: 힌트 감점을 반영한 최고 점수(0~100).
- `best_correct`, `best_total`: 최고 점수를 기록했을 때의 정답 수와 전체 문제 수.
- `has_played`: 점수 확인 시 플레이 기록이 있는지 판별합니다.
- `history`: 각 게임의 시간, 문제 수, 정답 수, 힌트 수, 점수 목록입니다.

저장 데이터는 `.gitignore`에 포함되어 개인 플레이 결과가 실수로 커밋되지 않습니다. 파일을 지우면 다음 실행 때 기본 퀴즈로 다시 시작합니다.

## Git 연습 참고

기능 단위로 변경을 기록하고 브랜치를 병합하는 예시입니다. GitHub 저장소에 코드를 올린 뒤 별도 폴더에서 복제하고, 원격 변경을 `pull`하는 연습도 할 수 있습니다.

```text
git add main.py test_main.py README.md .gitignore
git commit -m "Feat: 천문학 퀴즈 게임 구현"
git checkout -b feat/quiz-play
# 기능을 수정하고 테스트한 다음 커밋
git add main.py test_main.py
git commit -m "Feat: 퀴즈 플레이와 점수 기록 추가"
git checkout main
git merge feat/quiz-play
git clone <GitHub 저장소 URL> <복제할 폴더>
git pull
```
