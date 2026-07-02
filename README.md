# Sigma AI Guardian

Dự án quản lý phòng tin học có tích hợp AI để phân loại nội dung và hỗ trợ gọi tool trong ứng dụng.

## Cấu trúc chính

- `src/content_classifier/`: package chính cho bộ phân loại nội dung, có tài liệu chi tiết tại [`src/content_classifier/README.md`](src/content_classifier/README.md).
- `scripts/`: các script hỗ trợ tạo dữ liệu, huấn luyện và xử lý file.
- `data/`: dữ liệu train và model đã huấn luyện.
- `tests/content_classifier/`: bộ test cho các classifier.

## Yêu cầu

- Python 3.13 trở lên.
- Cài dependency từ [`requirements.txt`](requirements.txt).

## Ghi chú

- Thư mục `src/content_classifier` là package chính.
- Model runtime hiện nằm trong `data/models/`.
- Dữ liệu train hiện nằm trong `data/training/`.
