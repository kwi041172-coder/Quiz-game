import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from main import Quiz, QuizGame, SafeExit


class QuizTests(unittest.TestCase):
    def test_quiz_requires_four_choices_and_valid_answer(self) -> None:
        with self.assertRaises(ValueError):
            Quiz("문제", ["하나", "둘", "셋"], 1)
        with self.assertRaises(ValueError):
            Quiz("문제", ["하나", "둘", "셋", "넷"], 5)

    def test_quiz_checks_and_round_trips_json_data(self) -> None:
        quiz = Quiz("별은 무엇일까요?", ["별", "행성", "위성", "혜성"], 1, "스스로 빛나요.")

        self.assertTrue(quiz.is_correct(1))
        self.assertFalse(quiz.is_correct(2))
        self.assertEqual(Quiz.from_dict(quiz.to_dict()).hint, "스스로 빛나요.")


class QuizGameTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "state.json"
        self.output = io.StringIO()
        self.redirect = contextlib.redirect_stdout(self.output)
        self.redirect.__enter__()
        self.game = QuizGame(self.state_path)

    def tearDown(self) -> None:
        self.redirect.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_missing_file_uses_at_least_five_default_quizzes(self) -> None:
        self.assertGreaterEqual(len(self.game.quizzes), 5)
        self.assertFalse(self.game.has_played)

    def test_number_input_trims_and_retries_blank_bad_and_out_of_range(self) -> None:
        with patch("builtins.input", side_effect=["", "abc", "9", " 2 "]):
            result = self.game.read_number("선택: ", 1, 5)

        self.assertEqual(result, 2)
        self.assertIn("빈 입력", self.output.getvalue())
        self.assertIn("숫자를 입력", self.output.getvalue())
        self.assertIn("사이의 숫자", self.output.getvalue())

    def test_eof_requests_safe_exit(self) -> None:
        with patch("builtins.input", side_effect=EOFError):
            with self.assertRaises(SafeExit):
                self.game.read_text("입력: ")

    def test_keyboard_interrupt_requests_safe_exit(self) -> None:
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with self.assertRaises(SafeExit):
                self.game.read_text("입력: ")

    def test_corrupted_file_is_reset_to_default_data(self) -> None:
        self.state_path.write_text("{broken", encoding="utf-8")

        game = QuizGame(self.state_path)

        saved = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(len(game.quizzes), len(saved["quizzes"]))
        self.assertGreaterEqual(len(saved["quizzes"]), 5)
        self.assertIn("초기화", self.output.getvalue())

    def test_add_and_reload_quiz_and_score_history(self) -> None:
        self.game.quizzes.append(
            Quiz("새 문제", ["가", "나", "다", "라"], 2, "두 번째입니다.")
        )
        self.game._record_result(correct=3, total=4, hints_used=1, score=50)

        reloaded = QuizGame(self.state_path)

        self.assertEqual(reloaded.quizzes[-1].question, "새 문제")
        self.assertEqual(reloaded.best_score, 50)
        self.assertTrue(reloaded.has_played)
        self.assertEqual(len(reloaded.history), 1)

    def test_add_quiz_collects_inputs_and_saves(self) -> None:
        with patch(
            "builtins.input",
            side_effect=[" 새 문제 ", "가", "나", "다", "라", "2", "힌트"],
        ):
            self.game.add_quiz()

        self.assertEqual(self.game.quizzes[-1].question, "새 문제")
        self.assertEqual(self.game.quizzes[-1].answer, 2)
        self.assertTrue(self.state_path.exists())

    def test_play_records_hint_penalty_and_accepts_retried_answer(self) -> None:
        self.game.quizzes = [self.game.quizzes[0]]
        answer = self.game.quizzes[0].answer
        with (
            patch("main.random.sample", side_effect=lambda values, count: values[:count]),
            patch("builtins.input", side_effect=["1", "0", "h", "h", str(answer)]),
        ):
            self.game.play_quiz()

        self.assertEqual(self.game.best_score, 0)
        self.assertEqual(self.game.history[0]["hints_used"], 1)
        self.assertEqual(self.game.history[0]["correct"], 1)
        self.assertIn("새로운 최고 점수", self.output.getvalue())

    def test_empty_quiz_list_is_handled(self) -> None:
        self.game.quizzes = []

        self.game.play_quiz()
        self.game.list_quizzes()
        self.game.delete_quiz()

        self.assertIn("등록된 퀴즈가 없습니다", self.output.getvalue())
        self.assertIn("삭제할 퀴즈가 없습니다", self.output.getvalue())

    def test_menu_retries_invalid_choice_then_lists_and_exits(self) -> None:
        with patch("builtins.input", side_effect=["9", "3", "7"]):
            self.game.run()

        self.assertIn("1부터 7 사이", self.output.getvalue())
        self.assertIn("등록된 퀴즈 목록", self.output.getvalue())
        self.assertIn("종료합니다", self.output.getvalue())

    def test_cancelled_delete_keeps_quiz(self) -> None:
        original_count = len(self.game.quizzes)
        with patch("builtins.input", side_effect=["1", "n"]):
            self.game.delete_quiz()

        self.assertEqual(len(self.game.quizzes), original_count)
        self.assertFalse(self.state_path.exists())

    def test_invalid_delete_confirmation_reprompts(self) -> None:
        original_count = len(self.game.quizzes)
        with patch("builtins.input", side_effect=["1", "maybe", "y"]):
            self.game.delete_quiz()

        self.assertEqual(len(self.game.quizzes), original_count - 1)
        self.assertTrue(self.state_path.exists())
        self.assertIn("y 또는 n", self.output.getvalue())

    def test_save_failure_is_reported(self) -> None:
        blocking_path = Path(self.temp_dir.name) / "not-a-directory"
        blocking_path.write_text("block", encoding="utf-8")
        self.game.state_path = blocking_path / "state.json"

        self.assertFalse(self.game.save_data())
        self.assertIn("저장에 실패", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()
