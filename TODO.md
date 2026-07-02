# TODO
## Ưu tiên cao

- Sửa toàn bộ import đang trỏ sang path cũ để khớp với layout hiện tại.
- Đồng bộ `scripts/train_model.py` với `data/training/` và `data/models/`.
- Sửa `src/content_classifier/local/classifier.py` để dùng đúng model path hiện có và bỏ side effect lúc import.
- Sửa `tests/content_classifier/test_all_classifiers.py` để import đúng package trong `src/`.

## Ưu tiên trung bình

- Rà lại phần mô tả cách chạy script và test để tránh lệch so với code hiện tại.

## Ưu tiên thấp

- Điền nội dung cho các file tài liệu còn trống nếu chúng được xem là tài liệu chính thức của project.
