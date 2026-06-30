# dedupe_similar_lines.py

from difflib import SequenceMatcher
from pathlib import Path
from typing import List


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio() * 100


def remove_similar_lines(
    input_file: str,
    threshold: float,
    output_file: str | None = None,
    encoding: str = "utf-8",
) -> List[str]:
    path = Path(input_file)

    lines = path.read_text(encoding=encoding).splitlines()

    groups: List[List[str]] = []

    for line in lines:
        added = False

        for group in groups:
            if any(similarity(line, existing) >= threshold for existing in group):
                group.append(line)
                added = True
                break

        if not added:
            groups.append([line])

    result = []

    for group in groups:
        shortest = min(group, key=len)
        result.append(shortest)

    if output_file:
        Path(output_file).write_text("\n".join(result) + "\n", encoding=encoding)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Xóa các dòng giống nhau theo threshold %, chỉ giữ dòng ngắn nhất."
    )

    parser.add_argument("file", help="File input")
    parser.add_argument("threshold", type=float, help="Độ giống nhau, ví dụ 85")
    parser.add_argument("-o", "--output", help="File output")

    args = parser.parse_args()

    remove_similar_lines(
        input_file=args.file,
        threshold=args.threshold,
        output_file=args.output or args.file,
    )
