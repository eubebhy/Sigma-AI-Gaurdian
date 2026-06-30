Quy ước cấu trúc Package & Module
Package: Mỗi phương thức phân loại là một package nằm cùng cấp với file chạy chính, đặt tên theo cú pháp: <ten_phuong_phap>_classifier.

Hàm trong Module: Trong mỗi module con của package, chỉ chứa tối đa một hàm chính. Tất cả các hàm khác bắt buộc phải bắt đầu bằng dấu gạch dưới _.
Moi ham chinh trong cac package phuong thuc phai co dang nhu sau:

```
```
```python
from tags import ContentCatergory
def phuong_thuc_c_classifier(text: str) -> list[ContentCatergory]:
# ...
return result
```
```
```
