"""API chính của `content_classifier`.

File path: `src/content_classifier/__init__.py`
Input: text gốc cần phân loại.
Output: một `ContentCategory` duy nhất.
Nguyên lý: ưu tiên rule-based vì nhẹ và ổn định; nếu có lỗi khi chạy thì rơi về
local classifier. API này không trả về list để giữ kết quả nhất quán với các
engine con.
"""

from content_classifier.tags import ContentCategory


def rule_based_classifier(text: str) -> ContentCategory:
    from content_classifier.rule_based import rule_based_classifier as _classifier

    return _classifier(text)


def local_ai_classifier(text: str) -> ContentCategory:
    from content_classifier.local import local_ai_classifier as _classifier

    return _classifier(text)


def content_classifier(text: str) -> ContentCategory:
    try:
        return rule_based_classifier(text)
    except Exception:
        try:
            return local_ai_classifier(text)
        except Exception:
            return ContentCategory.Unknown
