# Web Blocker

`src/device_controler/web_blocker` chặn website bằng cách thêm domain vào hosts
file của hệ điều hành.

## Input

- `block(file_path)`: nhận file text chứa domain hoặc URL, mỗi dòng một giá trị.
- `unblock(file_path)`: nhận cùng format file để xoá domain khỏi block state.

## Output

- Hosts file được cập nhật trong block nằm giữa marker của SAG.
- Nếu nội dung không đổi, module không ghi lại hosts file.

## Nguyên lý

Module đọc danh sách domain, chuẩn hoá về hostname, đọc hosts hiện tại, thay đổi
block của SAG trong bộ nhớ rồi ghi atomic replace. Cách này giữ phần hosts bên
ngoài marker không thuộc quyền quản lý của module.

## Quyền hệ thống

- Linux: thường cần quyền ghi `/etc/hosts`.
- Windows: thường cần quyền admin để ghi `C:\Windows\System32\drivers\etc\hosts`.

for coding agents:
Very big file, don't read: ./porn-sites.txt
