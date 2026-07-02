from pathlib import Path

from content_classifier.local.ai_assistant import LocalAI
from content_classifier.tags import ContentCategory


def _map_label_to_category(label: str) -> ContentCategory | None:
    normalized_label = label.lower()
    if normalized_label == ContentCategory.Pornography.name.lower():
        return ContentCategory.Pornography
    if normalized_label == ContentCategory.Gore.name.lower():
        return ContentCategory.Gore
    if normalized_label == ContentCategory.Game.name.lower():
        return ContentCategory.Game
    if normalized_label == ContentCategory.Education.name.lower():
        return ContentCategory.Education
    if normalized_label == ContentCategory.Unknown.name.lower():
        return ContentCategory.Unknown
    return None


def local_ai_classifier(text: str) -> list[ContentCategory]:
    model_path = Path(__file__).resolve().parents[3] / "data" / "models" / "Ritchie.bin"
    ai = LocalAI(model_path=model_path)
    try:
        predictions = ai.predict(text)
    finally:
        ai.close()

    categories = [
        category
        for label in predictions
        if (category := _map_label_to_category(label)) is not None
    ]
    if categories:
        return categories

    return [ContentCategory.Unknown]
