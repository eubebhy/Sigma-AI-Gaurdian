import re


def replace_function(match: re.Match[str]) -> str:
    w1 = match.group(1)
    w2 = match.group(3)
    return f"{w1} {w2}" if len(w1) > 2 and len(w2) > 2 else f"{w1}{w2}"


def clean_text(text: str) -> str:
    sep_pattern = r"([a-zA-Z0-9]+)(_ |- |\. |/ |\\ |-|_|\.|/|\\)([a-zA-Z0-9]+)"
    text = re.sub(r"(?<=\b[a-zA-Z0-9])\s+(?=[a-zA-Z0-9]\b)", "", text)

    current_text = text
    while True:
        current_text, count = re.subn(
            sep_pattern,
            replace_function,
            current_text,
        )
        if count == 0:
            break

    print(f"\ncleaned text: {current_text}")
    return current_text
