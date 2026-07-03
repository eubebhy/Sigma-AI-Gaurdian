import re
import unicodedata
from collections.abc import Iterable


ZERO_WIDTH_CHARS = {
    "\u200b": "",
    "\u200c": "",
    "\u200d": "",
    "\ufeff": "",
    "\u2060": "",
}


CONFUSABLE_CHARS = {
    # Greek / Cyrillic common spoof chars
    "ο": "o",  # Greek omicron
    "Ο": "O",
    "о": "o",  # Cyrillic o
    "О": "O",
    "а": "a",
    "А": "A",
    "е": "e",
    "Е": "E",
    "і": "i",
    "І": "I",
    "Ι": "I",
    "ⅼ": "l",
    "Ι": "I",
    "р": "p",
    "Р": "P",
    "с": "c",
    "С": "C",
    "х": "x",
    "Х": "X",
}


LEET_CHARS = {
    "0": "o",
    "3": "e",
    "4": "a",
    "@": "a",
    "1": "i",
    "!": "i",
    "|": "i",
}


OCR_CHARS = {
    "I": "l",
    "L": "l",
}


SEP_CHARS = r"._/\\-"


GAME_PHRASES = {
    "black myth wukong",
    "path of exile",
    "steam",
    "epic games",
    "riot games",
    "valorant",
    "league of legends",
    "minecraft",
    "roblox",
    "genshin impact",
    "counter strike",
    "csgo",
    "cs2",
    "dota",
    "fortnite",
}


ADULT_PHRASES = {
    "spankbang",
    "onlyfans",
    "fansly",
    "camsoda",
    "chaturbate",
    "stripchat",
    "livejasmin",
    "myfreecams",
    "brazzers",
    "reality kings",
    "naughty america",
    "bangbros",
    "vixen",
    "digital playground",
    "fake taxi",
    "adult video",
    "hentai",
    "doujin",
    "bukkake",
    "rule34",
    "rule 34",
    "nhentai",
    "hentai haven",
    "jav",
    "uncensored jav",
}


GORE_PHRASES = {
    "crime scene photos",
    "crime scene photos uncensored",
    "fatal accident cctv",
    "raw battlefield casualties",
    "battlefield casualties",
    "animal attack graphic",
    "graphic accident",
    "graphic accident compilation",
    "graphic violence",
    "graphic violence compilation",
    "liveleak archive",
    "liveleak archive mirror",
    "medical trauma archive",
    "nsfl",
    "nsfl crash footage",
    "nsfl thread",
    "nsfl discussion",
    "crash footage",
    "fatal workplace accident",
    "surgical operation uncensored",
    "train accident graphic",
    "war combat footage graphic",
    "war combat footage",
    "beheading",
    "beheading video",
    "blood gore",
    "best gore",
    "cartel execution",
    "graphic violence compilation",
}


OBFUSCATED_WORDS = {
    "hentai",
    "doujin",
    "bukkake",
    "adult",
    "video",
    "spankbang",
    "onlyfans",
    "fansly",
    "camsoda",
    "chaturbate",
    "stripchat",
    "livejasmin",
    "myfreecams",
    "brazzers",
    "bangbros",
    "vixen",
    "nsfl",
    "gore",
    "blood",
    "graphic",
    "violence",
    "compilation",
    "beheading",
    "execution",
    "cartel",
    "combat",
    "footage",
    "battlefield",
    "casualties",
    "accident",
    "fatal",
    "crime",
    "scene",
    "photos",
}


def _translate_chars(text: str, table: dict[str, str]) -> str:
    return "".join(table.get(ch, ch) for ch in text)


def _normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _translate_chars(text, ZERO_WIDTH_CHARS)
    text = _translate_chars(text, CONFUSABLE_CHARS)
    return text


def _leet_normalize_token(token: str) -> str:
    return "".join(LEET_CHARS.get(ch, ch) for ch in token)


def _ocr_normalize_token(token: str) -> str:
    return "".join(OCR_CHARS.get(ch, ch) for ch in token)


def _soft_token_normalize(token: str) -> str:
    token = _leet_normalize_token(token)
    token = _ocr_normalize_token(token)
    return token


def _join_separator_split_words(text: str) -> str:
    pattern = (
        rf"(?<![^\W_])"
        rf"(?:[^\W_][{re.escape(SEP_CHARS)}])+[^\W_]"
        rf"(?![^\W_])"
    )

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        return re.sub(rf"[{re.escape(SEP_CHARS)}]", "", raw)

    return re.sub(pattern, repl, text, flags=re.UNICODE)


def _join_space_split_words(text: str) -> str:
    pattern = r"(?<![^\W_])(?:[^\W_]\s+){2,}[^\W_](?![^\W_])"

    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        joined = re.sub(r"\s+", "", raw)
        canonical = _soft_token_normalize(joined).lower()

        if canonical in OBFUSCATED_WORDS:
            return canonical

        return raw

    return re.sub(pattern, repl, text, flags=re.UNICODE)


def _replace_separator_between_words(text: str) -> str:
    pattern = (
        r"([^\W_]+)"
        r"(_ |- |\. |/ |\\ |-|_|\.|/|\\)"
        r"([^\W_]+)"
    )

    def repl(match: re.Match[str]) -> str:
        left = match.group(1)
        right = match.group(3)

        if len(left) == 1 or len(right) == 1:
            return left + right

        return left + " " + right

    current_text = text

    while True:
        current_text, count = re.subn(
            pattern,
            repl,
            current_text,
            flags=re.UNICODE,
        )
        if count == 0:
            break

    return current_text


def _normalize_obfuscated_tokens(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        raw = match.group(0)
        canonical = _soft_token_normalize(raw).lower()

        if canonical in OBFUSCATED_WORDS:
            return canonical

        return raw

    return re.sub(r"[^\W_@!|]+", repl, text, flags=re.UNICODE)


def _collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_text(text: str) -> str:
    text = _normalize_unicode(text)
    text = _join_separator_split_words(text)
    text = _join_space_split_words(text)
    text = _replace_separator_between_words(text)
    text = _normalize_obfuscated_tokens(text)
    text = _collapse_spaces(text)
    return text
