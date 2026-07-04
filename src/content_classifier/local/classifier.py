"""Bộ phân loại local.

File path: `src/content_classifier/local/classifier.py`
Input: text gốc cần phân loại.
Output: một `ContentCategory` duy nhất.
Nguyên lý: chuẩn hoá văn bản, chạy mô hình local, chọn nhãn có xác suất cao nhất
và rơi về `Unknown` khi kết quả không đủ rõ hoặc khi model trả về nhãn nội bộ
đã được gộp về `Unknown` trong quá trình train.
"""

from pathlib import Path
from typing import Final

from content_classifier.local.ai_assistant import LocalAI
from content_classifier.clean_obfuscate_text import clean_text
from content_classifier.tags import ContentCategory

UNKNOWN_MARGIN_THRESHOLD: Final[float] = 0.067
MODEL_LABEL_TO_CATEGORY: Final[dict[str, ContentCategory]] = {
    ContentCategory.Pornography.name.lower(): ContentCategory.Pornography,
    ContentCategory.Gore.name.lower(): ContentCategory.Gore,
    ContentCategory.Game.name.lower(): ContentCategory.Game,
    ContentCategory.Unknown.name.lower(): ContentCategory.Unknown,
}


def _map_label_to_category(label: str) -> ContentCategory | None:
    return MODEL_LABEL_TO_CATEGORY.get(label.lower())


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
        if top_probability - second_probability < UNKNOWN_MARGIN_THRESHOLD:
            return ContentCategory.Unknown

    category = _map_label_to_category(top_label)
    if category is not None:
        return category

    return ContentCategory.Unknown
