"""Bộ phân loại rule-based.

File path: `src/content_classifier/rule_based/__init__.py`
Input: text gốc cần phân loại.
Output: một `ContentCategory` duy nhất.
Nguyên lý: chuẩn hoá văn bản rồi dò từ khoá theo thứ tự ưu tiên; nhãn khớp đầu
tiên được trả về, nếu không khớp thì trả về `Unknown`.
"""

# Built in lib
from pathlib import Path
from typing import Any, cast

# Third party lib
from rapidfuzz import fuzz  # type: ignore[import-not-found]

# Project's modules
from content_classifier.clean_obfuscate_text import clean_text
from content_classifier.tags import ContentCategory


def _parse_keyword(keywords_file_path: str):
    """Ham nay lam viec theo quy uoc trong data/keywords/readme.txt"""
    with open(keywords_file_path, "r") as f:
        data = f.readlines()
    data = [part.lower().strip() for line in data for part in line.split("|")]
    return data


def _had_keyword(text: str, keyword_list: list[str], threshold: float = 100.0) -> bool:
    """
    Kiểm tra xem chuỗi text có chứa từ khóa nào (kể cả dính liền như xxxhentai)
    bằng thư viện rapidfuzz với cơ chế partial_ratio.
    """

    text = clean_text(text=text)
    text_lower = text.lower()
    fuzz_api = cast(Any, fuzz)

    for keyword in keyword_list:
        # fuzz.partial_ratio sẽ tự động tìm đoạn khớp nhất của keyword trong text_lower
        # Ví dụ: fuzz.partial_ratio("hentai", "xxxhentai") -> Kết quả: 100.0
        score = float(fuzz_api.partial_ratio(keyword.lower(), text_lower))
        if score >= threshold:
            return True

    return False


kw_dir = Path(__file__).parent / "keywords"

pornography_words = _parse_keyword(str(kw_dir / "pornography.txt"))
game_words = _parse_keyword(str(kw_dir / "game.txt"))
gore_words = _parse_keyword(str(kw_dir / "gore.txt"))


def rule_based_classifier(text: str) -> ContentCategory:
    if _had_keyword(text, pornography_words):
        return ContentCategory.Pornography

    if _had_keyword(text, game_words):
        return ContentCategory.Game

    if _had_keyword(text, gore_words):
        return ContentCategory.Gore

    return ContentCategory.Unknown
