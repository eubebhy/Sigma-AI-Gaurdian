# Built in lib
from pathlib import Path

# Third party lib
from rapidfuzz import fuzz

# Project's modules
from tags import ContentCategory
from content_classifier.clean_obfuscate_text import clean_text


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

    for keyword in keyword_list:
        # fuzz.partial_ratio sẽ tự động tìm đoạn khớp nhất của keyword trong text_lower
        # Ví dụ: fuzz.partial_ratio("hentai", "xxxhentai") -> Kết quả: 100.0
        if fuzz.partial_ratio(keyword.lower(), text_lower) >= threshold:
            return True

    return False


kw_dir = Path(__file__).parent / "keywords"

pornography_words = _parse_keyword(str(kw_dir / "pornography.txt"))
game_words = _parse_keyword(str(kw_dir / "game.txt"))
gore_words = _parse_keyword(str(kw_dir / "gore.txt"))


def rule_based_classifier(text: str) -> list[ContentCategory]:
    tags: list[ContentCategory] = []
    if _had_keyword(text, pornography_words):
        tags.append(ContentCategory.Pornography)

    if _had_keyword(text, game_words):
        tags.append(ContentCategory.Game)

    if _had_keyword(text, gore_words):
        tags.append(ContentCategory.Gore)

    if not tags:
        tags.append(ContentCategory.Unknown)

    return tags
