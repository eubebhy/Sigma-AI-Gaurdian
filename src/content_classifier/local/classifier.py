"""Bộ phân loại local.

File path: `src/content_classifier/local/classifier.py`
Input: text gốc cần phân loại.
Output: một `ContentCategory` duy nhất.
Nguyên lý: chuẩn hoá văn bản, chạy mô hình local, chọn nhãn có xác suất cao nhất
và rơi về `Unknown` khi kết quả không đủ rõ hoặc không map được sang enum nội bộ.
"""

from pathlib import Path

from content_classifier.local.ai_assistant import LocalAI
from content_classifier.clean_obfuscate_text import clean_text
from content_classifier.tags import ContentCategory

_UNKNOWN_MARGIN_THRESHOLD = 0.3


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


def local_ai_classifier(text: str) -> ContentCategory:
    model_path = Path(__file__).resolve().parents[3] / "data" / "models" / "Ritchie.pkl"
    ai = LocalAI(model_path=model_path)
    text = clean_text(text)
    try:
        predictions = ai.predict(text, k=2)
    finally:
        ai.close()

    ranked_predictions = list(predictions.items())
    if not ranked_predictions:
        return ContentCategory.Unknown

    top_label, top_probability = ranked_predictions[0]
    if len(ranked_predictions) > 1:
        _, second_probability = ranked_predictions[1]
        if top_probability - second_probability < _UNKNOWN_MARGIN_THRESHOLD:
            return ContentCategory.Unknown

    category = _map_label_to_category(top_label)
    if category is not None:
        return category

    return ContentCategory.Unknown
