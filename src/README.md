# Source Layout

`src/` chứa các package runtime của Sigma AI Guardian. Code trong thư mục này
được import bởi ứng dụng, script hỗ trợ và test.

## `device_controler`

Nhóm module điều khiển máy học sinh hoặc môi trường desktop.

- `browser_tab`: mở URL bằng browser phù hợp.
- `process_killer`: kill process theo blacklist.
- `screen_capture`: chụp màn hình bằng MSS.
- `screenlocker`: lock màn hình và chặn input.
- `web_blocker`: thêm/xoá domain trong hosts file.

Input/output chi tiết nằm trong docstring đầu từng module.

## `system_monitor`

Cung cấp API thu thập trạng thái hệ thống.

- `clipboard_tracker`: đọc clipboard hiện tại.
- `keylogger`: gom phím thành chuỗi text tạm thời.
- `windows_tracker`: đọc tiêu đề cửa sổ active và các cửa sổ đang mở.

## `utils`

Chứa chức năng dùng lại cho nhiều package, không phụ thuộc feature cấp cao.

- `input_blocker`: chặn/mở chặn input theo OS.
- `input_controller`: gửi và lắng nghe input cross-platform.

Packages in this directory are intended to be imported by other packages. They should not import feature packages or depend on higher-level project components.
Put new functionality here when more than one packages needs it.

## Rules

* The main APIs of all plugins and packages must not block the main thread.
* Long-running operations must run in daemon threads with `daemon=True`.
* Module phức tạp phải có docstring đầu file nêu `file path`, input, output và nguyên lý hoạt động.
