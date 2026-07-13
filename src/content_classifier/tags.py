"""Nhãn nội dung dùng chung cho toàn bộ hệ phân loại.

File path: `src/content_classifier/tags.py`
Input: không nhận input runtime; module chỉ định nghĩa enum dùng bởi classifier.
Output: `ContentCategory`, enum chuẩn để rule-based, local AI và caller trao đổi.

Nguyên lý hoạt động: mọi classifier phải trả về một giá trị trong enum này để API
tổng hợp ở `content_classifier.__init__` không phụ thuộc nhãn nội bộ của từng
engine. `Unknown` đại diện cho nội dung an toàn hoặc chưa đủ bằng chứng để chặn.
"""

from enum import Enum, auto


class ContentCategory(Enum):
    """Danh mục nội dung cuối cùng mà hệ thống có thể trả về."""

    Pornography = auto()
    Gore = auto()
    Unknown = auto()
    Game = auto()
