# `content_classifier`

Package này chứa các module phân loại nội dung của dự án.

## Thông tin module

- `file path`: `src/content_classifier/`
- `input`: chuỗi văn bản đầu vào cần phân loại.
- `output`: nhãn `ContentCategory` tương ứng với nội dung đầu vào.
- `nguyên lý hoạt động`: các classifier trong package này chuẩn hóa text, so khớp theo quy tắc hoặc suy luận từ model cục bộ, rồi trả về danh mục phù hợp.

## Thành phần

- `tags.py`: định nghĩa `ContentCategory`.
- `clean_obfuscate_text.py`: chuẩn hóa text trước khi so khớp từ khóa.
- `rule_based/`: classifier dựa trên từ khóa.
- `local/`: classifier chạy model scikit-learn cục bộ qua `joblib`.
- `cloud/`: chỗ dành cho classifier chạy qua dịch vụ cloud, hiện chưa triển khai.

## Quy ước

- Mỗi module chỉ nên làm một việc rõ ràng.
- Hàm nội bộ nên bắt đầu bằng `_`.
- Giữ tên file và tên package khớp với layout hiện tại trong `src/content_classifier/`.

```python
def classify(text: str) -> ContentCategory:
    """Phân loại văn bản đầu vào và trả về ContentCategory tương ứng."""
    pass
```

Sau do trong ./__init__.py se tong hop cac api phan loai lai va tao thanh 1 api duy nhat.
