<p align="center">
  <img src="sag-logo.png" alt="Sigma AI Guardian banner" width="700">
</p>

# Sigma AI Guardian

**Sigma AI Guardian (SAG)** là nền tảng quản lý phòng máy tích hợp AI, lấy cảm hứng từ các phần mềm như GoGuardian nhưng tập trung vào khả năng tự động hóa chủ động.

Thay vì chỉ giám sát và chặn nội dung, SAG có thể tự phân loại nội dung, phát hiện rủi ro, cảnh báo người dùng và thực hiện các tác vụ tự động thông qua AI.

## Tính năng

* Phân loại nội dung bằng AI chạy cục bộ (Local AI Text Classifier)
* Không yêu cầu kết nối Internet
* Không cần API Key
* Không cần đăng ký tài khoản
* Tự động phát hiện nội dung không phù hợp (ví dụ: khiêu dâm, bạo lực, game...)
* Rule-based filtering kết hợp AI để tăng độ chính xác
* Hỗ trợ gọi công cụ (Tool Calling) để tự động hóa tác vụ trong ứng dụng
* Hỗ trợ sử dụng LLM cục bộ hoặc thông qua API
* Thiết kế theo dạng module, dễ mở rộng thêm bộ phân loại và AI backend mới

## Kiến trúc

* **Rule-based Engine**: phát hiện nhanh bằng từ khóa và luật.
* **Local AI Classifier**: mô hình học máy chạy hoàn toàn trên máy người dùng.
* **LLM Backend**: hỗ trợ AI cục bộ hoặc các mô hình thông qua API.
* **Tool Calling**: cho phép AI chủ động thực hiện các hành động được ứng dụng cho phép.

## Mục tiêu

* Hoạt động hoàn toàn ngoại tuyến khi cần.
* Giảm tối đa phụ thuộc vào dịch vụ bên thứ ba.
* Dễ tích hợp vào phần mềm quản lý phòng máy.
* Dễ mở rộng và bảo trì.

## Yêu cầu

* Python 3.13 (khuyến nghị)
* Các thư viện trong `requirements.txt`

## Cài đặt

Đang hoàn thiện.
