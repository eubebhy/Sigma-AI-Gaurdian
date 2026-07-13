# Scripts hỗ trợ

Các script trong thư mục này phục vụ phát triển, train model và kiểm tra cục bộ.
Chúng không phải public runtime API của ứng dụng.

## Build dữ liệu train

- `dedupe_similar_lines.py`: xóa các dòng giống nhau theo threshold.
- `record_clip_board.py`: ghi nội dung clipboard vào file.
- `train_model.py`: huấn luyện model từ dữ liệu train hiện có.

## Khác

- `clean_pyright_check.sh`: chạy Pyright theo cách rút gọn để dễ đọc lỗi.

## Ghi chú

- Chạy script từ project root để các path tương đối trỏ đúng dữ liệu trong repo.
- Script ghi dữ liệu hoặc train model có thể tạo/thay đổi file trong `data/`.
- Khi sửa file Python, dùng `scripts/clean_pyright_check.sh <path>` để kiểm tra riêng file đó.
