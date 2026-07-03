from content_classifier.tags import ContentCategory
from content_classifier.local import local_ai_classifier
from content_classifier.rule_based import rule_based_classifier

"""
_CLASSIFIERS = {
    Classifier.RULE_BASED: rule_based_classifier,
    Classifier.LOCAL_AI: local_ai_classifier,
}


def content_classifier(text: str) -> ContentCategory:
    config = Config.get()

    for classifier in config.classifiers:
        try:
            result = _CLASSIFIERS[classifier](text)
        except Exception as e:
            continue  # Skip to the next classifier if an error occurs
"""
