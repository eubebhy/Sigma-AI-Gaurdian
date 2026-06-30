import argparse
import random
import sys
from pathlib import Path
from typing import Callable

CASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CASE_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tags import ContentCategory


THEME_ORDER = ("game", "porn", "gore", "safe")
THEME_TO_EXPECTED = {
    "game": [ContentCategory.Game],
    "porn": [ContentCategory.Pornography],
    "gore": [ContentCategory.Gore],
    "safe": [ContentCategory.Unknown],
}
MODE_CHOICES = ("all", "game", "porn", "gore")
CASE_PICK_CHOICES = ("sequential", "random")


def parse_arguments():
    _ = parser = argparse.ArgumentParser(
        description="Tester for all content classifiers"
    )
    _ = parser.add_argument(
        "-r", "--rule-based-engine", help="Test rule-based engine", action="store_true"
    )
    _ = parser.add_argument(
        "-l",
        "--local-ai-classifier",
        help="Test local AI classifier",
        action="store_true",
    )
    _ = parser.add_argument(
        "-c",
        "--cloud-ai-classifier",
        help="Test cloud AI classifier",
        action="store_true",
    )

    _ = parser.add_argument(
        "-f",
        "--show-failures",
        action="store_true",
        help="Show failed test cases and failure summary lines",
    )
    _ = parser.add_argument(
        "-m",
        "--mode",
        choices=MODE_CHOICES,
        default="all",
        help="Select which theme set to test",
    )
    _ = parser.add_argument(
        "-p",
        "--pick-mode",
        choices=CASE_PICK_CHOICES,
        default="sequential",
        help="Choose cases sequentially or randomly from each selected theme",
    )
    _ = parser.add_argument(
        "-n",
        "--sample-size",
        type=int,
        default=10,
        help="Maximum number of cases to take from each selected theme",
    )

    return parser.parse_known_args()


args, _ = parse_arguments()


def _strip_inline_comment(line: str) -> str:
    return line.split("#", 1)[0].strip()


def _load_cases_from_file(
    file_path: Path, expected_tags: list[ContentCategory]
) -> list[tuple[str, list[ContentCategory], str]]:
    test_cases: list[tuple[str, list[ContentCategory], str]] = []

    with file_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            text = _strip_inline_comment(raw_line)
            if not text:
                continue
            test_cases.append((text, expected_tags, file_path.stem))

    return test_cases


def _select_theme_names(mode: str) -> tuple[str, ...]:
    if mode == "all":
        return THEME_ORDER
    return (mode,)


def _sample_cases(
    cases: list[tuple[str, list[ContentCategory], str]],
    sample_size: int,
    pick_mode: str,
) -> list[tuple[str, list[ContentCategory], str]]:
    if sample_size < 0:
        sample_size = 0

    limit = min(sample_size, len(cases))
    if pick_mode == "random":
        return random.sample(cases, limit)

    return cases[:limit]


def load_test_cases(
    mode: str, sample_size: int, pick_mode: str
) -> list[tuple[str, list[ContentCategory], str]]:
    test_cases: list[tuple[str, list[ContentCategory], str]] = []

    for theme in _select_theme_names(mode):
        file_path = CASE_DIR / f"{theme}.txt"
        expected_tags = THEME_TO_EXPECTED[theme]
        cases = _load_cases_from_file(file_path, expected_tags)
        test_cases.extend(_sample_cases(cases, sample_size, pick_mode))

    return test_cases


class BaseClassifierTest:
    def run_classifier_test(
        self,
        engine_name: str,
        classifier_func: Callable[[str], list[ContentCategory]],
        test_cases: list[tuple[str, list[ContentCategory], str]],
    ):
        total_cases = len(test_cases)
        passed_count = 0
        failed_count = 0
        theme_stats = {
            theme: {"total": 0, "passed": 0, "failed": 0} for theme in THEME_ORDER
        }
        failed_cases: list[
            tuple[str, str, list[ContentCategory], list[ContentCategory]]
        ] = []

        print(f"=== {engine_name} ===")

        for text, expected_tags, theme in test_cases:
            actual_tags = classifier_func(text)
            is_passed = actual_tags == expected_tags

            theme_stats[theme]["total"] += 1
            if is_passed:
                passed_count += 1
                theme_stats[theme]["passed"] += 1
            else:
                failed_count += 1
                theme_stats[theme]["failed"] += 1
                failed_cases.append((theme, text, expected_tags, actual_tags))

            if is_passed or args.show_failures:
                status = "PASS" if is_passed else "FAIL"
                print(
                    f"[{status}][{theme}] {text} | expected={expected_tags[0].name} | got={actual_tags[0].name if actual_tags else 'Empty'}"
                )

        print()
        print("Summary")
        print(f"Total: {total_cases} | Passed: {passed_count} | Failed: {failed_count}")
        for theme in THEME_ORDER:
            stats = theme_stats[theme]
            print(
                f"{theme:>5}: {stats['passed']}/{stats['total']} passed, {stats['failed']} failed"
            )

        if args.show_failures and failed_cases:
            print("Failures")
            for theme, text, expected_tags, actual_tags in failed_cases:
                got = actual_tags[0].name if actual_tags else "Empty"
                print(
                    f"[{theme}] {text} | expected={expected_tags[0].name} | got={got}"
                )


def run_selected_tests():
    tester = BaseClassifierTest()
    test_cases = load_test_cases(args.mode, args.sample_size, args.pick_mode)

    if args.rule_based_engine:
        try:
            from content_classifier.rule_based_engine import rule_based_classifier
        except ModuleNotFoundError as exc:
            print("=== rule-based-engine ===")
            print(f"TODO: rule-based engine is unavailable: {exc}")
        else:
            tester.run_classifier_test(
                "rule-based-engine", rule_based_classifier, test_cases
            )

    if args.local_ai_classifier:
        try:
            from content_classifier.local_ai_backend import local_ai_classifier
        except ModuleNotFoundError as exc:
            print("=== local-ai-classifier ===")
            print(f"TODO: local AI backend is unavailable: {exc}")
        else:
            tester.run_classifier_test(
                "local-ai-classifier", local_ai_classifier, test_cases
            )

    if args.cloud_ai_classifier:
        print("=== cloud-ai-classifier ===")
        print("TODO: cloud AI backend is not wired into this test harness yet.")


if __name__ == "__main__":
    if not any(
        [args.rule_based_engine, args.local_ai_classifier, args.cloud_ai_classifier]
    ):
        print("Vui lòng truyền tham số để chọn engine cần test (-r, -l, hoặc -c).")
        sys.exit(0)

    run_selected_tests()
