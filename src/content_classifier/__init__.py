"""API chính của `content_classifier`.

File path: `src/content_classifier/__init__.py`
Input: text gốc cần phân loại.
Output: một `ContentCategory` duy nhất.
Nguyên lý: chạy rule-based và local classifier rồi hợp nhất kết quả. Nội dung
cấm là mọi nhãn khác `Unknown`; nếu cả hai engine đều phát hiện nội dung cấm
thì ưu tiên rule-based vì match theo luật thường rõ ràng hơn AI.
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
        rule_result = rule_based_classifier(text)
    except Exception:
        rule_result = ContentCategory.Unknown

    try:
        local_result = local_ai_classifier(text)
    except Exception:
        local_result = ContentCategory.Unknown

    if rule_result != ContentCategory.Unknown:
        return rule_result

    if local_result != ContentCategory.Unknown:
        return local_result

    return ContentCategory.Unknown
