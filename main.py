"""A beginner-friendly astronomy quiz game for the terminal."""

import json
import random
from datetime import datetime
from pathlib import Path


STATE_FILE = Path(__file__).resolve().parent / "state.json"


class SafeExit(Exception):
    """Raised when the user requests or triggers a safe shutdown."""


class Quiz:
    """One multiple-choice quiz question."""

    def __init__(
        self,
        question: str,
        choices: list[str] | tuple[str, ...],
        answer: int,
        hint: str = "문제의 핵심 개념을 떠올려 보세요.",
    ) -> None:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("문제는 비어 있을 수 없습니다.")
        if not isinstance(choices, (list, tuple)) or len(choices) != 4:
            raise ValueError("선택지는 정확히 4개여야 합니다.")
        if any(not isinstance(choice, str) or not choice.strip() for choice in choices):
            raise ValueError("선택지는 비어 있을 수 없습니다.")
        if type(answer) is not int or not 1 <= answer <= 4:
            raise ValueError("정답 번호는 1부터 4까지의 정수여야 합니다.")
        if not isinstance(hint, str) or not hint.strip():
            raise ValueError("힌트는 비어 있을 수 없습니다.")

        self.question = question.strip()
        self.choices = tuple(choice.strip() for choice in choices)
        self.answer = answer
        self.hint = hint.strip()

    def show(self, number: int | None = None) -> None:
        """Print the question and its four choices."""
        label = f"[문제 {number}]" if number is not None else "[퀴즈]"
        print(f"\n{label} {self.question}")
        for choice_number, choice in enumerate(self.choices, start=1):
            print(f"  {choice_number}. {choice}")

    def is_correct(self, answer: int) -> bool:
        return answer == self.answer

    def to_dict(self) -> dict[str, object]:
        return {
            "question": self.question,
            "choices": list(self.choices),
            "answer": self.answer,
            "hint": self.hint,
        }

    @classmethod
    def from_dict(cls, data: object) -> "Quiz":
        if not isinstance(data, dict):
            raise ValueError("퀴즈 항목은 객체여야 합니다.")
        return cls(
            question=data.get("question"),
            choices=data.get("choices"),
            answer=data.get("answer"),
            hint=data.get("hint", "문제의 핵심 개념을 떠올려 보세요."),
        )


class QuizGame:
    """Manage quizzes, gameplay, scores, and JSON persistence."""

    def __init__(self, state_path: Path = STATE_FILE) -> None:
        self.state_path = Path(state_path)
        self.quizzes = self.default_quizzes()
        self.best_score: int | None = None
        self.best_correct: int | None = None
        self.best_total: int | None = None
        self.has_played = False
        self.history: list[dict[str, object]] = []
        self.load_data()

    @staticmethod
    def default_quizzes() -> list[Quiz]:
        return [
            Quiz(
                "태양계에서 태양에 가장 가까운 행성은 무엇일까요?",
                ["금성", "수성", "지구", "화성"],
                2,
                "태양계에서 가장 작은 행성이기도 합니다.",
            ),
            Quiz(
                "태양계에서 가장 큰 행성은 무엇일까요?",
                ["토성", "천왕성", "목성", "해왕성"],
                3,
                "거대한 대적점으로도 유명합니다.",
            ),
            Quiz(
                "지구의 자연 위성 이름은 무엇일까요?",
                ["달", "타이탄", "유로파", "포보스"],
                1,
                "한 달의 이름과도 관련이 있습니다.",
            ),
            Quiz(
                "태양이 에너지를 만드는 주된 과정은 무엇일까요?",
                ["화학 연소", "핵융합", "핵분열", "마찰"],
                2,
                "가벼운 원자핵들이 합쳐지는 반응입니다.",
            ),
            Quiz(
                "붉은 행성이라고 불리는 행성은 무엇일까요?",
                ["목성", "금성", "화성", "수성"],
                3,
                "표면의 산화철 때문에 붉게 보입니다.",
            ),
            Quiz(
                "지구 대기에서 가장 많은 비율을 차지하는 기체는 무엇일까요?",
                ["산소", "이산화탄소", "수소", "질소"],
                4,
                "대기의 약 78%를 차지하는 기체입니다.",
            ),
            Quiz(
                "토성의 눈에 띄는 특징은 무엇일까요?",
                ["거대한 고리", "푸른 바다", "두 개의 태양", "긴 꼬리"],
                1,
                "얼음과 암석 조각으로 이루어져 있습니다.",
            ),
            Quiz(
                "우리 태양계가 속한 은하의 이름은 무엇일까요?",
                ["안드로메다 은하", "소용돌이 은하", "우리은하", "대마젤란은하"],
                3,
                "밤하늘에서 희미한 띠처럼 보이는 '은하수'의 고향입니다.",
            ),
        ]

    def load_data(self) -> None:
        if not self.state_path.exists():
            print("저장 파일이 없어 기본 천문학 퀴즈를 불러왔습니다.")
            return

        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            self._load_state(data)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as error:
            print(f"저장 파일을 읽을 수 없습니다 ({error}). 기본 데이터로 초기화합니다.")
            self.quizzes = self.default_quizzes()
            self.best_score = None
            self.best_correct = None
            self.best_total = None
            self.has_played = False
            self.history = []
            self.save_data()
            return

        print(
            f"저장 데이터를 불러왔습니다. "
            f"(퀴즈 {len(self.quizzes)}개, 최고 점수 "
            f"{self.best_score if self.best_score is not None else '기록 없음'})"
        )

    def _load_state(self, data: object) -> None:
        if not isinstance(data, dict):
            raise ValueError("저장 데이터의 최상위 값은 객체여야 합니다.")

        quizzes_data = data.get("quizzes")
        if not isinstance(quizzes_data, list):
            raise ValueError("quizzes 항목이 없거나 목록이 아닙니다.")
        quizzes = [Quiz.from_dict(item) for item in quizzes_data]

        best_score = data.get("best_score")
        if best_score is not None and (
            type(best_score) is not int or not 0 <= best_score <= 100
        ):
            raise ValueError("best_score는 0부터 100까지의 정수여야 합니다.")

        best_correct = data.get("best_correct")
        best_total = data.get("best_total")
        if best_correct is not None and (
            type(best_correct) is not int or best_correct < 0
        ):
            raise ValueError("best_correct 값이 올바르지 않습니다.")
        if best_total is not None and (type(best_total) is not int or best_total < 1):
            raise ValueError("best_total 값이 올바르지 않습니다.")
        if (best_correct is None) != (best_total is None):
            raise ValueError("최고 점수의 정답 수와 전체 문제 수가 함께 있어야 합니다.")

        has_played = data.get("has_played", best_score is not None)
        if type(has_played) is not bool:
            raise ValueError("has_played 값이 올바르지 않습니다.")

        history = data.get("history", [])
        if not isinstance(history, list):
            raise ValueError("history 항목은 목록이어야 합니다.")
        for record in history:
            self._validate_history_record(record)

        self.quizzes = quizzes
        self.best_score = best_score
        self.best_correct = best_correct
        self.best_total = best_total
        self.has_played = has_played
        self.history = history

    @staticmethod
    def _validate_history_record(record: object) -> None:
        if not isinstance(record, dict):
            raise ValueError("점수 기록 항목은 객체여야 합니다.")
        if not isinstance(record.get("played_at"), str):
            raise ValueError("점수 기록의 날짜가 올바르지 않습니다.")
        total = record.get("total")
        correct = record.get("correct")
        hints_used = record.get("hints_used")
        score = record.get("score")
        if type(total) is not int or total < 1:
            raise ValueError("점수 기록의 전체 문제 수가 올바르지 않습니다.")
        if type(correct) is not int or not 0 <= correct <= total:
            raise ValueError("점수 기록의 정답 수가 올바르지 않습니다.")
        if type(hints_used) is not int or not 0 <= hints_used <= total:
            raise ValueError("점수 기록의 힌트 사용 수가 올바르지 않습니다.")
        if type(score) is not int or not 0 <= score <= 100:
            raise ValueError("점수 기록의 점수가 올바르지 않습니다.")

    def save_data(self) -> bool:
        data = {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
            "best_correct": self.best_correct,
            "best_total": self.best_total,
            "has_played": self.has_played,
            "history": self.history,
        }
        temporary_path = self.state_path.with_suffix(self.state_path.suffix + ".tmp")

        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary_path.replace(self.state_path)
        except (OSError, TypeError) as error:
            print(f"저장에 실패했습니다 ({error}). 데이터가 디스크에 반영되지 않았습니다.")
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError as cleanup_error:
                print(f"임시 파일 정리에도 실패했습니다 ({cleanup_error}).")
            return False
        return True

    @staticmethod
    def read_text(prompt: str) -> str:
        while True:
            try:
                value = input(prompt).strip()
            except (KeyboardInterrupt, EOFError) as error:
                print("\n입력이 중단되어 안전하게 종료합니다.")
                raise SafeExit from error
            if value:
                return value
            print("빈 입력은 사용할 수 없습니다. 다시 입력해 주세요.")

    @classmethod
    def read_number(cls, prompt: str, minimum: int, maximum: int) -> int:
        while True:
            value = cls.read_text(prompt)
            try:
                number = int(value)
            except ValueError:
                print("숫자를 입력해 주세요.")
                continue
            if not minimum <= number <= maximum:
                print(f"{minimum}부터 {maximum} 사이의 숫자를 입력해 주세요.")
                continue
            return number

    def show_menu(self) -> None:
        print(
            "\n"
            "========================================\n"
            "       별빛 탐험대: 천문학 퀴즈\n"
            "========================================\n"
            "  1. 퀴즈 풀기\n"
            "  2. 퀴즈 추가\n"
            "  3. 퀴즈 목록\n"
            "  4. 최고 점수 확인\n"
            "  5. 점수 기록 확인\n"
            "  6. 퀴즈 삭제\n"
            "  7. 종료\n"
            "========================================"
        )

    def run(self) -> None:
        while True:
            self.show_menu()
            selection = self.read_number("메뉴를 선택하세요 (1-7): ", 1, 7)
            if selection == 1:
                self.play_quiz()
            elif selection == 2:
                self.add_quiz()
            elif selection == 3:
                self.list_quizzes()
            elif selection == 4:
                self.show_best_score()
            elif selection == 5:
                self.show_history()
            elif selection == 6:
                self.delete_quiz()
            else:
                print("별빛 탐험을 종료합니다. 다음에 또 만나요!")
                return

    def play_quiz(self) -> None:
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다. 먼저 퀴즈를 추가해 주세요.")
            return

        total = self.read_number(
            f"몇 문제를 풀까요? (1-{len(self.quizzes)}): ", 1, len(self.quizzes)
        )
        selected_quizzes = random.sample(self.quizzes, total)
        correct_count = 0
        hints_used = 0

        print(f"\n퀴즈를 시작합니다! 총 {total}문제입니다.")
        for question_number, quiz in enumerate(selected_quizzes, start=1):
            quiz.show(question_number)
            used_hint = False
            while True:
                value = self.read_text("정답 번호 (1-4, h=힌트): ").lower()
                if value == "h":
                    if used_hint:
                        print("이 문제의 힌트는 이미 확인했습니다.")
                    else:
                        print(f"힌트: {quiz.hint}")
                        used_hint = True
                    continue
                try:
                    answer = int(value)
                except ValueError:
                    print("1부터 4까지의 숫자 또는 h를 입력해 주세요.")
                    continue
                if not 1 <= answer <= 4:
                    print("정답 번호는 1부터 4 사이여야 합니다.")
                    continue
                break

            if used_hint:
                hints_used += 1
            if quiz.is_correct(answer):
                correct_count += 1
                print("정답입니다!")
            else:
                print(f"아쉽습니다. 정답은 {quiz.answer}번입니다.")

        earned_points = max(0, correct_count - hints_used)
        score = round(earned_points / total * 100)
        print(
            f"\n결과: {total}문제 중 {correct_count}문제 정답, "
            f"힌트 {hints_used}회 사용, 최종 점수 {score}점"
        )
        self._record_result(correct_count, total, hints_used, score)

    def _record_result(
        self, correct: int, total: int, hints_used: int, score: int
    ) -> None:
        self.has_played = True
        self.history.append(
            {
                "played_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "total": total,
                "correct": correct,
                "hints_used": hints_used,
                "score": score,
            }
        )
        if self.best_score is None or score > self.best_score:
            self.best_score = score
            self.best_correct = correct
            self.best_total = total
            print("새로운 최고 점수입니다!")
        self.save_data()

    def add_quiz(self) -> None:
        print("\n새로운 퀴즈를 추가합니다.")
        question = self.read_text("문제를 입력하세요: ")
        choices = [
            self.read_text(f"선택지 {number}: ") for number in range(1, 5)
        ]
        answer = self.read_number("정답 번호 (1-4): ", 1, 4)
        hint = self.read_text("힌트: ")
        self.quizzes.append(Quiz(question, choices, answer, hint))
        if self.save_data():
            print("퀴즈를 추가하고 저장했습니다.")
        else:
            print("퀴즈는 이번 실행 중에만 추가되었습니다.")

    def list_quizzes(self) -> None:
        if not self.quizzes:
            print("등록된 퀴즈가 없습니다.")
            return
        print(f"\n등록된 퀴즈 목록 (총 {len(self.quizzes)}개)")
        for number, quiz in enumerate(self.quizzes, start=1):
            print(f"  {number}. {quiz.question}")

    def show_best_score(self) -> None:
        if not self.has_played:
            print("아직 퀴즈를 푼 기록이 없습니다.")
            return
        print(
            f"최고 점수: {self.best_score}점 "
            f"({self.best_correct}/{self.best_total} 정답)"
        )

    def show_history(self) -> None:
        if not self.history:
            print("아직 점수 기록이 없습니다.")
            return
        print(f"\n점수 기록 (총 {len(self.history)}회)")
        for number, record in enumerate(self.history, start=1):
            print(
                f"  {number}. {record['played_at']} | "
                f"{record['correct']}/{record['total']} 정답 | "
                f"힌트 {record['hints_used']}회 | {record['score']}점"
            )

    def delete_quiz(self) -> None:
        if not self.quizzes:
            print("삭제할 퀴즈가 없습니다.")
            return
        self.list_quizzes()
        number = self.read_number(
            f"삭제할 퀴즈 번호 (1-{len(self.quizzes)}): ",
            1,
            len(self.quizzes),
        )
        while True:
            confirmation = self.read_text(
                f"'{self.quizzes[number - 1].question}' 퀴즈를 삭제할까요? (y/n): "
            ).lower()
            if confirmation in ("y", "yes", "n", "no"):
                break
            print("y 또는 n으로 답해 주세요.")
        if confirmation in ("n", "no"):
            print("삭제를 취소했습니다.")
            return

        removed_quiz = self.quizzes.pop(number - 1)
        if self.save_data():
            print("퀴즈를 삭제하고 저장했습니다.")
        else:
            self.quizzes.insert(number - 1, removed_quiz)
            print("저장에 실패해 퀴즈 삭제를 취소했습니다.")


def main() -> None:
    game = QuizGame()
    try:
        game.run()
    except SafeExit:
        print("현재까지의 저장 데이터를 보존하고 종료합니다.")
    finally:
        game.save_data()


if __name__ == "__main__":
    main()
