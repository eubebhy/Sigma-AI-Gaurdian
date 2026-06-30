# AGENTS.md

## Mission
- Project nay la phan mem quan ly phong tin hoc cho giao vien co tich hop ai de phan tich + tool call
ban chat no la Agent trong hinh hai app quan ly tinh hoc voi cac tinh nang co ban cua app quan ly phong
tin + AI tu dong hoa.

## rules
- Moi khi dinh lam gi day: kiem tra xem user co yeu cau khong. Neu user khong yeu cau thi dung ngay lap tuc
- Neu m vua bat dau chay va doc file nay, ngay lap tuc hoi user dang lam phan nao cua du an, nhan duoc cau tra loi
vi du nhung dang lam phan cac api lay thong tin may tinh, v.v
Hoi dang lam toi dau de nam bat context, pham vi lam viec 
- Sau khi xac dinh duoc pham vi lam viec, code m viet co the khong chay duoc, nhung no phai hoang thanh muc tieu truoc mat
Dung vi vai dong code chua chay duoc ma mo rong scope sang pham vi khac
- Neu code o tinh nang hien tai chua chay duoc vi thieu tinh nang khac, hay code tam bo de chay duoc tai cho + NOTE TODO
lam tinh nang con thieu thay vi lam luon trong phien lam viec hien tai 

## Authority
- Chỉ làm đúng task được yêu cầu.
- Không tự refactor.
- Không đổi architecture.
- Không thêm dependency nếu chưa được yêu cầu.
- Không sửa file ngoài phạm vi task.

## Coding rules
- Follow existing style.
- Minimal diff.
- Không đổi tên API public.
- Không tạo abstraction mới nếu không cần.

## Workflow
1. Đọc code liên quan.
2. Chỉ sửa file cần thiết.
3. Chạy test.
4. Nếu test fail thì sửa.
5. Không merge nhiều thay đổi vào một task.

## Done
Task chỉ hoàn thành khi:
- Build pass.
- Test pass.
- Không còn TODO mới.
