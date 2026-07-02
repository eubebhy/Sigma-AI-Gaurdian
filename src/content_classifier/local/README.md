# `content_classifier.local`

Nhóm module này phụ trách classifier chạy model FastText cục bộ.

## Thành phần

- `ai_assistant.py`: wrapper lazy-load model và dự đoán.
- `classifier.py`: lớp/hàm bọc mức cao hơn để gọi local AI classifier.

## Dữ liệu liên quan

- Model runtime hiện được lưu trong `data/models/`.
- Dữ liệu train dùng cho model nằm trong `data/training/`.

## Ghi chú

- Giữ module gọn, tránh tạo thêm file nếu chưa thật sự cần.
- Nếu `fasttext` thiếu type stub, chỉ ignore đúng dòng báo lỗi liên quan đến thư viện này.
